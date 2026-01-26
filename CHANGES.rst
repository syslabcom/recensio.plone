Changelog
=========


2.0.1 (unreleased)
------------------

- Nothing changed yet.


2.0.0 (2026-01-26)
------------------

- Tested on Python 3.10 and Python 3.13 [ale-rt]
- Avoid computing ``listAuthorsAndEditors`` twice
  `#3678 <https://github.com/syslabcom/scrum/issues/3678>`_
- Set redirect-to-publication as default view for Issue and Volume
  `#3151 <https://github.com/syslabcom/scrum/issues/3151>`_
- Fix ResourceWarning on unclosed file handles in tests [gyst]
- Upgrade github CI pre-commit action to 3.0.1 [gyst]
- Fix the CI build [gyst]
- Upgrade to Plone 6.1.3 [ale-rt, reinhardt, gyst]
- Update the pre-commit linters [gyst]
- Don't error out on main nav on a clean install [gyst]
- Upgrade ftw.upgrade to the SLC patched version [gyst]
- Add collective.solr and make the eea.facetednavigation view compatible with that [gyst]
- Activate fulltext PDF solr search, provide upgrade, adjust tests [gyst]
- Bugfix PublicationsViewlet for the Plone upgrade [gyst]
- Add parameter -asxhtml to tidy to fix pdf generation of html reviews [pilz]
- Performance improvements
  `#3678 <https://github.com/syslabcom/scrum/issues/3678>`_
  [ale-rt]
- Fix the ``sehepunkte-import`` view
  `#4071 <https://github.com/syslabcom/scrum/issues/4071>`_
  [ale-rt]

1.0.6 (2025-05-22)
------------------

- Fix mangled issue PDF in bulk upload
  `#3152 <https://github.com/syslabcom/scrum/issues/3152>`_
  [reinhardt]


1.0.5 (2025-03-28)
------------------

- Fix errors caused by missing person references
  `#3373 <https://github.com/syslabcom/scrum/issues/3373>`_
  [reinhardt]


1.0.4 (2025-02-10)
------------------

- Performance improvements
  `#3067 <https://github.com/syslabcom/scrum/issues/3067>`_
  [ale-rt]


1.0.3 (2024-07-30)
------------------

- Fixed error when editing keywords
  `#2408 <https://github.com/syslabcom/scrum/issues/2408>`_
  [reinhardt]


1.0.2 (2024-07-26)
------------------

- Improved performance when editing keywords
  `#2408 <https://github.com/syslabcom/scrum/issues/2408>`_
  [reinhardt]


1.0.1 (2024-07-09)
------------------

- Support changing PDF watermark image on publication.
  `#2385 <https://github.com/syslabcom/scrum/issues/2385>`_
  [reinhardt]


1.0.0 (2024-06-12)
------------------

- Initial release.
  [thet]
