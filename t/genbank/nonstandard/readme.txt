These genbank files have nonstandard formats (compare to each other,
and to sample1.gbk, in ../standard/).  They should produce warnings
or errors.

sample2.gbk - missing quotes around some string fields, and has
  user-added qualifiers (e.g., /cog)
  Old behavior:
    Throws an exception and fails to parse.
  New behavior
    Warn user about ignoring the user-defined fields

sample3.gbk - unbalanced double quotes around a multi-line string field
  This throws an exception and fails to parse.

sample4.gbk - unbalanced double quotes around a single line string field
  Old behavior:
    Parses incorrectly (adds an extra quote)
  New behavior
    Throws an exception and fails to parse.

sample5.gbk - unbalanced double quotes around a single line string field
  (counterpart to sample4)
  This throws an exception and fails to parse.

sample6.gbk - unbalanced double quotes around a multi-line string field
  (counterpart to sample3)
  Old behavior:
    Parses incorrectly (adds an extra quote)
  New behavior
    Throws an exception and fails to parse.
