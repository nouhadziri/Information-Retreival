import string

from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

enhanced_punctuation = string.punctuation + \
                       u'\u2012' + u'\u2013' + u'\u2014' + u'\u2015' + u'\u2018' + u'\u2019' + u'\u201C' + u'\u201D' + \
                       u'\u2212' + u'\u2026'
translate_table = dict((ord(char), u'') for char in enhanced_punctuation)

stemmer = PorterStemmer()


def is_stopword(word):
    return word in stopwords.words('english')


def normalize(word):
    """
    converts terms in lower case, drops stop words and applies stemming using
    the PorterStemmer algorithm

    :param word:
    :return:
    """
    term = word.lower()

    if is_stopword(term):
        raise Warning("stopwords are not normalized here")

    term = stemmer.stem(term.encode('utf-8').decode('utf-8').translate(translate_table))

    if not term:
        raise RuntimeWarning("after normalization word became empty")

    return term

