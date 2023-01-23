from functools import reduce


def getFormatter(*specification):
    """
    Give the specification as a list of separators.
    Returns a method that accepts n+1 attributes and joins them if the
    attribute is not empty.

    The tests have been moved to the tests module.

    >>> formatter = getFormatter(', ', ', ', ' to ')
    >>> formatter('1','2','3','4')
    '1, 2, 3 to 4'
    >>> formatter('1',None,None, '2')
    '1 to 2'
    >>> formatter('1',None,'2',None)
    '1, 2'
    >>> formatter(None, None, '1', '2')
    '1 to 2'
    >>> formatter('1', '2')
    '1, 2'
    >>> formatter(None, None, None, None)
    ''

    Because we have complex requirements, here is a real example:
    [Rezensent Nachname], [Rezensent Vorname]: review of: [Werkautor Nachname], [Werkautor Vorname], [Werktitel]. [Werk-Untertitel], [Erscheinungsort]: [Verlag], [Jahr], in: [Zs-Titel], [Nummer], [Heftnummer (gezähltes Jahr/Erscheinungsjahr)], URL recensio.
    >>> rezensent_nachname, rezensent_vorname, werkautor_nachname, werkautor_vorname, werktitel, werk_untertitel, erscheinungsort, verlag, jahr, zs_titel, nummer, heftnummer, gezaehltes_jahr, erscheinungsjahr, url_recensio = 'rezensent_nachname', 'rezensent_vorname', 'werkautor_nachname', 'werkautor_vorname', 'werktitel', 'werk_untertitel', 'erscheinungsort', 'verlag', 'jahr', 'zs_titel', 'nummer', 'heftnummer', 'gezaehltes_jahr', 'erscheinungsjahr', 'url_recensio'
    >>> example_args = rezensent_nachname, rezensent_vorname, werkautor_nachname, werkautor_vorname, werktitel, werk_untertitel, erscheinungsort, verlag, jahr, zs_titel, nummer, heftnummer, gezaehltes_jahr, erscheinungsjahr, url_recensio

    >>> rezensent = getFormatter(', ')
    >>> item = getFormatter(', ', ', ', '. ', ', ', ': ', ', ')
    >>> mag_year = getFormatter('/')
    >>> mag_number_and_year = getFormatter(', ', ', ', ' ')
    >>> full_citation_inner = getFormatter(': review of: ', ', in: ', ', ')
    >>> def full_citation(*args):
    ...     rezensent_string = rezensent(*args[0:2])
    ...     item_string = item(*args[2:9])
    ...     mag_year_string = mag_year(*args[12:14])
    ...     mag_year_string = mag_year_string and '(' + mag_year_string + ')' or None
    ...     mag_number_and_year_string = mag_number_and_year(args[9], args[10], args[11], mag_year_string)
    ...     return full_citation_inner(rezensent_string, item_string, mag_number_and_year_string, args[14])
    >>> full_citation(*example_args)
    'rezensent_nachname, rezensent_vorname: review of: werkautor_nachname, werkautor_vorname, werktitel. werk_untertitel, erscheinungsort: verlag, jahr, in: zs_titel, nummer, heftnummer (gezaehltes_jahr/erscheinungsjahr), url_recensio'

    >>> def copy_with_some_nones(args, *missings):
    ...     retval = [x for x in args]
    ...     for missing in missings:
    ...         retval[missing] = None
    ...     return retval

    >>> no_mag_year = copy_with_some_nones(example_args, 12, 13)
    >>> full_citation(*no_mag_year)
    'rezensent_nachname, rezensent_vorname: review of: werkautor_nachname, werkautor_vorname, werktitel. werk_untertitel, erscheinungsort: verlag, jahr, in: zs_titel, nummer, heftnummer, url_recensio'

    >>> no_rezensent = copy_with_some_nones(example_args, 0, 1)
    >>> full_citation(*no_rezensent)
    'werkautor_nachname, werkautor_vorname, werktitel. werk_untertitel, erscheinungsort: verlag, jahr, in: zs_titel, nummer, heftnummer (gezaehltes_jahr/erscheinungsjahr), url_recensio'
    """  # noqa: E501

    def joinIfNotEmpty(remainder, joiner_and_new_string):
        joiner, new_string = joiner_and_new_string
        if not remainder:
            return new_string or ""
        if not new_string:
            return remainder or ""
        return joiner.join((remainder, new_string))

    def formatter(*args):
        data_to_reduce = [args[0]] + list(zip(specification, args[1:]))
        return reduce(joinIfNotEmpty, data_to_reduce)

    return formatter
