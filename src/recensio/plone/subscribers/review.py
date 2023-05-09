from logging import getLogger
from plone import api
from plone.base.utils import safe_bytes
from plone.base.utils import safe_text
from plone.namedfile import NamedBlobImage
from plone.namedfile.file import NamedBlobFile
from shutil import which
from string import Template
from tempfile import NamedTemporaryFile

import glob
import os
import subprocess
import tempfile


# XXX restore me
# RUN_SHELL_COMMANDS = os.environ.get("RUN_SHELL_COMMANDS", False)
RUN_SHELL_COMMANDS = True

logger = getLogger(__name__)

HTML_TEMPLATE = Template(
    """
<!DOCTYPE html>
<html>
<body>$body</body>
</html>
""".strip()
)


class SubprocessException(Exception):
    """For exceptions from RunSubprocess."""

    def __init__(self, message="empty"):
        self.message = message

    def __str__(self):
        return repr(self.message)


class RunSubprocess:
    """Wrapper for external command line utilities.

    Creates temporary files/directories as required and helps remove
    them afterwards.

    Usage:
    $ pdftk /path/to/file.pdf burst output /path/to/output_%%04d.pdf
    gen_thumbs = RunSubprocess("pdftk")
    gen_thumbs.create_tmp_input(suffix=".pdf", data=<pdf data>)
    gen_thumbs.create_tmp_output_dir()
    gen_thumbs.output_params = "burst output"
    gen_thumbs.run()
    if gen_thumbs.errors == None:
        result = gen_thumbs.output_path
    gen_thumbs.clean_up()
    """

    def __init__(
        self,
        program_name,
        extra_paths=None,
        input_path="",
        input_params="",
        output_params="",
        output_path="",
    ):
        if not RUN_SHELL_COMMANDS:
            raise SubprocessException(
                "The RUN_SHELL_COMMANDS environment variable is unset or "
                "False. Ignoring expensive shell commands."
            )
        self.program_name = program_name
        self.program = which(program_name)
        if extra_paths:
            # Before we had a custom implementation of which, but now we use shutil.which,
            # that has a path parameter but I noticed that in the old code it seemed to be
            # never used
            raise NotImplementedError(
                "extra_paths search has not been implemented yet and probably will never be"
            )

        if self.program is None:
            raise SubprocessException("Unable to find the %s program" % (program_name))
        self.tmp_input = None
        self.tmp_output = None
        self.tmp_output_dir = None
        self.input_path = input_path
        self.input_params = input_params
        self.output_params = output_params
        self.output_path = ""
        self.errors = ""
        self.cmd = ""

    def _create_tmp_file(self, prefix="", suffix="", data=None):
        """Create a temporary file as input for the command."""
        fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
        tmp_file = os.fdopen(fd, "bw")
        if data:
            tmp_file.write(data)
        tmp_file.close()
        return path

    def create_tmp_input(self, prefix="", suffix="", data=None):
        self.input_path = self._create_tmp_file(prefix=prefix, suffix=suffix, data=data)

    def create_tmp_ouput(self, prefix="", suffix="", data=None):
        self.tmp_output = self._create_tmp_file(prefix=prefix, suffix=suffix, data=data)

    def create_tmp_output_dir(self, **kw):
        self.tmp_output_dir = tempfile.mkdtemp(**kw)

    def run(self, input_params="", input_path="", output_params="", output_path=""):
        """Run the command."""

        if input_params != "":
            self.input_params = input_params

        if input_path != "":
            self.input_path = input_path
        elif self.input_path == "":
            self.input_path = self.tmp_input

        if output_params != "":
            self.output_params = output_params

        if output_path != "":
            self.output_path = output_path
        elif self.output_path == "":
            self.output_path = True and self.tmp_output or self.tmp_output_dir

        self.cmd = (
            [self.program]
            + self.input_params.split()
            + [self.input_path]
            + self.output_params.split()
            + [self.output_path]
        )
        logger.info("Running the following command:\n %s" % " ".join(self.cmd))

        process = subprocess.Popen(
            self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        stdoutdata, stderrdata = process.communicate()

        returncode = process.returncode

        if returncode:
            raise RuntimeError(" ".join([str(returncode), safe_text(stderrdata)]))

        if stderrdata:
            stderrdata = safe_text(stderrdata)
            if "Error" in stderrdata:
                logger.error(stderrdata)
            else:
                logger.info(stderrdata)

    def clean_up(self):
        """Remove any temporary files which have been created."""
        for tmp in [self.tmp_input, self.tmp_output]:
            if tmp is not None and os.path.exists(tmp):
                os.remove(tmp)

        if self.tmp_output_dir is not None:
            tmp_dir = self.tmp_output_dir
            for tmp_file in os.listdir(tmp_dir):
                os.remove(os.path.join(tmp_dir, tmp_file))
            os.removedirs(tmp_dir)


def SimpleSubprocess(*cmd, **kwargs):
    """Run a sub process, return all output, retval[0] is stdout, retval[1] ist
    stderr If the process run failed, raise an Exception cmd imput arg is
    supposed to be a list with the command and the passed arguments."""
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdoutdata, stderrdata = process.communicate()
    except OSError as e:
        raise RuntimeError(str(e))

    returncode = process.returncode

    if returncode not in kwargs.get("exitcodes", [0]):
        raise RuntimeError(" ".join([str(returncode), stderrdata]))

    return stdoutdata, stderrdata


def update_generated_pdf(obj):
    """If there isn't a custom pdf version of the review, generate the pdf from
    an Office document file, (anything supported by abiword).

    If there isn't an Office file then generate the pdf from the
    contents of the review text (html)
    """
    has_custom_pdf = getattr(obj, "pdf", None) and obj.pdf.getSize() > 0
    if not has_custom_pdf:
        # Generate the pdf file and save it as a blob
        try:
            create_pdf = RunSubprocess(
                "abiword",
                input_params="--plugin=AbiCommand -t pdf",
                output_params="-o",
            )
            create_pdf.create_tmp_ouput()
            doc = getattr(obj, "doc", None)
            if doc:
                with doc.open() as open_blob:
                    blob_path = open_blob.name
                create_pdf.run(input_path=blob_path)
            else:
                review = obj.review
                # Insert the review into a template so we have a
                # valid html file
                if not review:
                    return
                data = HTML_TEMPLATE.substitute(body=review.output_relative_to(obj))

                with NamedTemporaryFile() as tmp_input:
                    with NamedTemporaryFile() as tmp_output:
                        tmp_input.write(safe_bytes(data))
                        tmp_input.flush()
                        try:
                            SimpleSubprocess(
                                "tidy",
                                "-utf8",
                                "-numeric",
                                "-o",
                                tmp_output.name,
                                tmp_input.name,
                                exitcodes=[0, 1],
                            )
                            tmp_output.seek(0)
                            data = tmp_output.read()
                        except RuntimeError:
                            logger.error(
                                "Tidy was unable to tidy the html for %s",
                                obj.absolute_url(),
                                exc_info=True,
                            )
                    create_pdf.create_tmp_input(suffix=".html", data=data)
                try:
                    create_pdf.run()
                except RuntimeError:
                    logger.error(
                        "Abiword was unable to generate a pdf for %s and created an error pdf",
                        obj.absolute_url(),
                        exc_info=True,
                    )
                    create_pdf.create_tmp_input(
                        suffix=".html", data="Could not create PDF"
                    )
                    create_pdf.run()

            with open(create_pdf.output_path, "br") as pdf_file:
                pdf_data = pdf_file.read()

            create_pdf.clean_up()

            obj.generatedPdf = NamedBlobFile(
                filename=f"{obj.id}.pdf",
                data=pdf_data,
            )
        except SubprocessException:
            logger.error(
                "The application Abiword does not seem to be available",
                exc_info=True,
            )


def _getAllPageImages(context, size=(320, 452)):
    """Generate the preview images for a pdf."""
    review_view = api.content.get_view(name="review_view", context=context)
    pdf = review_view.get_review_pdf()
    if pdf:
        with pdf["blob"].open() as f:
            pdf_data = f.read()
    if not pdf or not pdf_data:
        return "%s has no pdf" % (context.absolute_url()), None
    else:
        # Split the pdf, one file per page
        try:
            split_pdf_pages = RunSubprocess("pdftk", output_params="burst output")
        except SubprocessException as e:
            return e
        split_pdf_pages.create_tmp_input(suffix=".pdf", data=pdf_data)
        split_pdf_pages.create_tmp_output_dir()
        split_pdf_pages.output_path = os.path.join(
            split_pdf_pages.tmp_output_dir, "%04d.pdf"
        )
        split_pdf_pages.run()

        msg = tuple()
        if split_pdf_pages.errors != "":
            msg += ("Message from split_pdf_pages:" "\n%s\n" % split_pdf_pages.errors,)

        # Convert the pages to .gifs
        # rewritten to have one converter step per page as we have seen process
        # sizes larger than 2GB for 60 pages in a batch
        for filename in glob.glob(split_pdf_pages.tmp_output_dir + "/*.pdf"):
            pdf_to_image = RunSubprocess(
                "convert",
                input_params="-density 250",
                input_path=filename,
                output_params="-resize %sx%s -background white -flatten"
                % (size[0], size[1]),
            )
            outputname = ".".join(filename.split("/")[-1].split(".")[:-1]) + ".gif"
            pdf_to_image.output_path = os.path.join(
                split_pdf_pages.tmp_output_dir, outputname
            )
            pdf_to_image.run()
            if pdf_to_image.errors != "":
                msg += ("Message from pdfs_to_images:" "\n%s\n" % pdf_to_image.errors,)

            pdf_to_image.clean_up()

        imgfiles = [
            gif
            for gif in os.listdir(split_pdf_pages.tmp_output_dir)
            if os.path.splitext(gif)[1] == ".gif"
        ]
        imgfiles.sort()

        pages = []
        for img in imgfiles:
            with open(os.path.join(split_pdf_pages.tmp_output_dir, img), "br") as img:
                pages.append(img.read())

        # Remove temporary files
        split_pdf_pages.clean_up()

        if pages:
            imgfields = []
            for idx, img in enumerate(pages):
                IF = NamedBlobImage(
                    filename=f"{context.id}_page_{idx}.gif",
                    data=img,
                )
                imgfields.append(IF)
            setattr(context, "pagePictures", imgfields)

        return msg or "Successfully converted %s pages" % len(pages)


class ReviewPDF:
    """Adapter to generate a cover image from a review's PDF data."""

    def __init__(self, context):
        self.context = context

    def __str__(self):
        return "<recensio.contenttypes {} title={}>".format(
            self.__class__.__name__,
            self.context.Title(),
        )

    __repr__ = __str__

    def generatePageImages(self, later=True):
        """Generate an image for each page of the pdf."""
        result = ""
        status = 1
        result = _getAllPageImages(self.context, (800, 1131))

        if result:
            logger.warning("popen: %r", result)
            if "Error:" in result:
                status = 0

        return status


def review_pdf_updated_eventhandler(obj, evt):
    """Re-generate the pdf version of the review, then update the cover image
    of the pdf if necessary."""
    if not obj.REQUEST.get("pdf_file"):
        update_generated_pdf(obj)

    # Terrible hack, if this method gets called without a real
    # object, we assume that the caller wants htis to happen now
    ReviewPDF(obj).generatePageImages(later=evt is not None)
