# Memory-warrant audit — instructions

Each item shows a clinical research question (intervention vs comparator on an
outcome), the ANNOTATED EVIDENCE from the source article that answers it, and a
short MEMORY note written by an automated pipeline. Judge the memory ONLY
against the annotated evidence; do not use outside knowledge.

Answer four yes/no questions per item (write Y or N):

1. target_present   — Does the memory mention this specific outcome for this
                       comparison at all (even vaguely)?
2. direction_correct — If it does, is the direction of effect stated in the memory
                       the same as in the evidence (increase / decrease / no
                       difference)? Write N if the memory states a different
                       direction OR states no direction at all. N/A if not present.
3. stat_status_preserved — Is the statistical status preserved: a significant
                       finding is still presented as a real effect, a
                       non-significant / "no difference" finding is NOT presented
                       as an effect (and vice versa)? N/A if not present.
4. complete_warrant — Would a reader of the memory ALONE reach the same
                       conclusion about this question as a reader of the
                       evidence, with the same confidence? This is Y only if 1-3
                       are all Y and nothing in the memory contradicts or hedges
                       the finding away.

Optional free-text `note`.
Items are in random order; the pipeline condition is hidden on purpose.
