
"""
WORDLIST.PY

Be careful with the format here. An entry is a pair of strings,
i.e. is two strings included in round brackets: ("bar", "noun>agr")

The first of these strings is the morpheme, the second is its
category. "noun>agr" describes a noun looking for an agreement marker
to its right (i.e. what I gave in the notes as
"noun/agr"). "(noun>agr)<(verb>tns)" describes a "(noun>agr)" looking
for a "(verb>tns)" to its left, i.e. as something that I would have
written as "(noun/agr)\(verb/tns)". I've changed from "/" and "\" to
">" and "<" because using "\" in Python strings is a nightmare
(because it's an escape character, so you end up writing loads of
things like "(noun/agr)\\(verb/tns)", and in the end this just becomes
unmanageable).

It's very easy to get lost: put the brackets inside the string quotes,
forget the commas, ... So be careful.

I've grouped them sort of thematically. All the open class words first,
then each of the different affix types together. You don't have to do
this, but it will make your life easier when developing your
dictionary and mine when I am marking.
"""
WORDS = [("bar", "noun>agr"), ("bat", "noun>agr"), ("bard", "noun>agr"), ("battle", "noun>agr"),
         ("car", "noun>agr"), ("cat", "noun>agr"), ("cart", "noun>agr"), ("card", "noun>agr"), ("cattle", "noun>agr"), 
         ("catch", "noun>agr"), ("chase", "verb>tns"),
         ("construct", "verb>tns"),
         ("dry", "verb>tns"), ("dry", "adj>cmp"),
         ("fair", "adj>cmp"),
         ("happy", "adj>cmp"),
         ("kiss", "noun>agr"), ("kiss", "verb>tns"), 
         ("song", "noun>agr"), ("sing", "verb>tns"), 
         ("terrible", "adj>cmp"),
         ("vile", "adj>cmp"),
         ("walk", "verb>tns"), ("work", "verb>tns"),
         
         ("er", "(noun>agr)<(verb>tns)"), 
         ("er", "cmp"), ("est", "cmp"), ("ly", "cmp"), ("", "cmp"),
         ("ed", "tns"), ("ing", "tns"), ("s", "tns"), ("", "tns"), 
         ("s", "agr"), ("", "agr"),
         ("re", "(verb>tns)>(verb>tns)"),
         ("ation", "(noun>agr)<(verb>tns)"),
         ("un", "(adj>cmp)>(adj>cmp)"),]
