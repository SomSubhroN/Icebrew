### Advanced Group Analysis

Icebrew supports classical and heteroscedastic one-way analysis of variance, together with pairwise post-hoc comparison procedures.

**One-way ANOVA** evaluates whether the means of multiple independent groups differ. It assumes independent observations, approximately normally distributed residuals, and homogeneity of variance.

**Welch's ANOVA** evaluates differences in group means without assuming equal population variances. It remains sensitive to violations of independence and distributional assumptions.

**Tukey HSD** provides pairwise comparisons while controlling the family-wise error rate under its assumptions, particularly equal variances and independent observations.

**Games–Howell** supports pairwise comparisons under unequal variances and potentially unequal group sizes.

Icebrew also provides multiple-testing corrections:

- **Bonferroni:** Controls family-wise error through a conservative adjustment.
- **Holm:** Step-down family-wise error correction.
- **Benjamini–Hochberg (BH):** Controls the false discovery rate under its applicable assumptions.

Statistical significance should not be interpreted independently of effect size, study design, assumptions, sample size, and the scientific context. ANOVA and post-hoc procedures do not establish causality.