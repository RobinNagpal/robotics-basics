# A worked example

This page follows this solution through real numbers. It starts with the hard
case, a glass that cannot be pushed safely. Then it follows one table through
the whole method. An example that shows only the easy case would teach the
wrong lesson.

## Contents

1. [When a glass cannot be pushed safely](#1-when-a-glass-cannot-be-pushed-safely)
2. [A worked example](#2-a-worked-example)

## 1. When a glass cannot be pushed safely

The hard case comes first, because it decides which glasses the model never
sees. A glass tips if the jaw touches it too high for its foot and the
friction. [Pushing without
toppling](../01_the-problem/05_pushing-without-toppling.md) explains that rule
once, for every solution.

**The model is never asked about a refusal.** A glass can be refused for two
reasons. Either it would tip, or every push for it clashes with a neighbour,
leaves the zone or leaves the arm's reach. Both reasons leave the glass with no
candidate pushes. **Ranking an empty list still gives an empty list.**

The refusals were counted. Over the fifty held-out tables, this solution refused
143 of the 251 glasses, the same number as the printed rule. Its own
`results.json` gives the reasons:

- 47 glasses tipped when the 5 mm test push was tried;
- 41 glasses would tip before they slide, so they were not pushed;
- 43 glasses were still without room after pushing;
- 9 glasses had nowhere clear to be pushed;
- 3 glasses were left because another glass on the table had fallen over.

So tipping causes 88 of the 143 refusals. The model can do nothing about any
of them, because they are settled before it is asked.

The hard case is clear. The next section follows an easier table, where the
model does get a list to order.

## 2. A worked example

The previous section showed glasses the model never sees. This section follows
one table where it does see pushes. The idea is easier to see once the list of
pushes has a shape.

**The table.** Four tapered glasses stand in the glass zone. They have
different sizes. Two of them stand well clear of everything. The other two
stand too close together, so neither has the room the open jaw needs. The room
test measures to the neighbour's edge, not its middle. So the narrower glass of
the pair is more crowded, because its wider neighbour reaches further into the
gap.

**Two glasses leave first.** The two glasses that already have room are racked.
So the planner now has a table of two glasses, not four. This is the cheapest
step, and it happens first on every table.

**The tipping test runs next, and it cannot decide.** For both glasses, the
answer depends on the friction, which nobody knows. So the arm makes a 5 mm
test push on each glass and looks before and after. Both glasses slide, so the
run goes on. A glass that failed the test would be refused, and the model would
never see it.

**The geometry lists many pushes.** For each glass, the enumerator tries 72
headings and steps out in 2 mm steps up to 150 mm. It drops every step where a
path clashes, or the end point leaves the zone or the reach. Many pushes are
left. On the training tables, the middle crowded glass has 84 candidates, and
the middle whole-table decision has 261.

**Only a few of them finish the job.** For each glass, these fall in two
groups. One group points roughly away from the neighbour. The other points
round the neighbour the other way. Each heading gives at most one such push, so
each glass has at most 72.

**All of them score the same.** Each one leaves both glasses with room, so each
gets the same label. Each one ends just past the line it had to clear, plus the
10 mm aiming margin, because the enumerator stops each heading as soon as the
push works. Over 161 such groups on the training tables, the best and worst
push in a group differ by 0.0 mm of room at the median. They differ only in how
far the glass travels, and the geometry already knows that distance.

**The printed rule takes the shortest one.** A model can agree with that choice.
It can disagree and pick a longer push. Or it can take longer to give the same
answer. It can do nothing else, because these pushes all have the same label.

**The model only has something to say about the other pushes.** Each glass also
has many pushes that ease the crowding without finishing the job. These do
differ. The same measurement puts the best and worst of them 11.9 mm of room
apart at the median. Their real result depends most on friction and on how the
weight sits under the glass. A ranker is not asked about those quantities.
[Solution 4](../07_a-world-model-then-plan-with-it/01_what-it-is.md) fits a
model of exactly them.

This example showed what the model gets to choose from. The next page, [what it
needs](05_what-it-needs.md), lists what the solution costs to run.

← [How it works](03_how-it-works.md) · [What it needs](05_what-it-needs.md) →
