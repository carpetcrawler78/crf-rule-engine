/* =========================================================================
   run_demo.sas - run the demo study end to end in SAS
   (works in SAS 9.4M3+ and SAS OnDemand for Academics)

   Set &root to the folder that contains this repository.
   ========================================================================= */

%let root = /home/u0000000/crf-rule-engine;   /* <-- adjust */

%include "&root./sas/crf_rule_engine.sas";

/* 1. Excel rules -> generated SAS program */
%crf_rules_to_sas(
    rules = &root./rules/demo_fu12_rules.xlsx,
    sheet = fu12_rules,
    code  = &root./sas/generated/demo_fu12_checks_from_sas.sas
);

/* 2. load the generated program and run it on the raw scanner export */
%include "&root./sas/generated/demo_fu12_checks_from_sas.sas";

%crf_clean(
    raw    = &root./data/demo_fu12_raw.csv,
    outlib = work,
    outdir = &root./output
);

/* 3. look at the results */
proc print data=work.summary noobs; run;
proc freq data=work.findings order=freq;
  tables variable * type / list nocum;
run;
