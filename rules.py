
factsAndRules = """
q(X, Y) ==> r(Y, X).
a(X) & x(f(X), Y) & y(Y) ==> p(X, [Y]).
a(X) & b(Y) & c(X, Y) ==> q(X, Y).

b(X) ==> x(X).
a(9).
a(7).
b(10).
b(8).
c(7, 8).
c(9, 10).

x(f(X), X).
y(0).
y(9).


loves([loves, [X], [Y]]) ==> knows([knows, [X], [Y]]).

"""

