from plone.dexterity.content import Container
from plone.namedfile.field import NamedBlobImage
from plone.supermodel import model
from recensio.plone import _
from zope.interface import implementer


class IPublication(model.Schema):
    """Marker interface and Dexterity Python Schema for Publication."""

    pdf_watermark = NamedBlobImage(
        title=_("label_publication_pdf_watermark", default="PDF watermark"),
        description=_(
            "description_publication_pdf_watermark",
            default=(
                "Upload a publication logo for the PDF coversheet. Transparent PNG "
                "format images are recommended."
            ),
        ),
        required=False,
    )


@implementer(IPublication)
class Publication(Container):
    """Content-type class for IPublication."""
