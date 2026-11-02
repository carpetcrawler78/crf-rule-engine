/* ---------------------------------------------------------------------
   GENERATED CODE - do not edit by hand. Change demo_fu12_rules.xlsx and regenerate.
   Generated 2026-11-02 by crf-rule-engine. 25 fields, 23 rules.
   ------------------------------------------------------------------ */

%macro crf_clean(raw=, outlib=work, outdir=);

/* 1. Read the export: every field as text, so nothing is lost silently */
data _crf_raw;
  infile "&raw." dlm="|" dsd truncover firstobs=2 lrecl=32767;
  length _r1-_r25 $200;
  input _r1-_r25;
run;

/* 2. Convert according to the format codes, record format findings */
data _crf_typed(drop=_r: variable value type rule message)
     _crf_fmt(keep=id variable value type rule message);
  set _crf_raw;
  length variable $32 value $200 type $6 rule $500 message $200;
  _n_fmt = 0;
  length fu12_newdx_txt $50;
  length fu12_med1 $50;
  length fu12_med2 $50;
  length scan_user $12;
  /* id: +"0"N(4) */
  id = input(strip(_r1), ?? best32.);
  if not missing(_r1) and missing(id) then do;
    variable="id"; value=_r1; type="format"; rule='+"0"N(4)'; message="not numeric"; _n_fmt + 1; output _crf_fmt;
  end;
  else if length(scan(strip(_r1), 1, '.')) > 4 then do;
    variable="id"; value=_r1; type="format"; rule='+"0"N(4)'; message="more than 4 digits"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_day: +"0"N(0-2) */
  fu12_day = input(strip(_r2), ?? best32.);
  if not missing(_r2) and missing(fu12_day) then do;
    variable="fu12_day"; value=_r2; type="format"; rule='+"0"N(0-2)'; message="not numeric"; _n_fmt + 1; output _crf_fmt;
  end;
  else if length(scan(strip(_r2), 1, '.')) > 2 then do;
    variable="fu12_day"; value=_r2; type="format"; rule='+"0"N(0-2)'; message="more than 2 digits"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_month: +"0"N(0-2) */
  fu12_month = input(strip(_r3), ?? best32.);
  if not missing(_r3) and missing(fu12_month) then do;
    variable="fu12_month"; value=_r3; type="format"; rule='+"0"N(0-2)'; message="not numeric"; _n_fmt + 1; output _crf_fmt;
  end;
  else if length(scan(strip(_r3), 1, '.')) > 2 then do;
    variable="fu12_month"; value=_r3; type="format"; rule='+"0"N(0-2)'; message="more than 2 digits"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_year: +"0"N(0-4) */
  fu12_year = input(strip(_r4), ?? best32.);
  if not missing(_r4) and missing(fu12_year) then do;
    variable="fu12_year"; value=_r4; type="format"; rule='+"0"N(0-4)'; message="not numeric"; _n_fmt + 1; output _crf_fmt;
  end;
  else if length(scan(strip(_r4), 1, '.')) > 4 then do;
    variable="fu12_year"; value=_r4; type="format"; rule='+"0"N(0-4)'; message="more than 4 digits"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_age: +"0"N(0-3) */
  fu12_age = input(strip(_r5), ?? best32.);
  if not missing(_r5) and missing(fu12_age) then do;
    variable="fu12_age"; value=_r5; type="format"; rule='+"0"N(0-3)'; message="not numeric"; _n_fmt + 1; output _crf_fmt;
  end;
  else if length(scan(strip(_r5), 1, '.')) > 3 then do;
    variable="fu12_age"; value=_r5; type="format"; rule='+"0"N(0-3)'; message="more than 3 digits"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_health: +"0"N(1) */
  fu12_health = input(strip(_r6), ?? best32.);
  if not missing(_r6) and missing(fu12_health) then do;
    variable="fu12_health"; value=_r6; type="format"; rule='+"0"N(1)'; message="not numeric"; _n_fmt + 1; output _crf_fmt;
  end;
  else if length(scan(strip(_r6), 1, '.')) > 1 then do;
    variable="fu12_health"; value=_r6; type="format"; rule='+"0"N(1)'; message="more than 1 digits"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_sym_a: +"0"N(1) */
  fu12_sym_a = input(strip(_r7), ?? best32.);
  if not missing(_r7) and missing(fu12_sym_a) then do;
    variable="fu12_sym_a"; value=_r7; type="format"; rule='+"0"N(1)'; message="not numeric"; _n_fmt + 1; output _crf_fmt;
  end;
  else if length(scan(strip(_r7), 1, '.')) > 1 then do;
    variable="fu12_sym_a"; value=_r7; type="format"; rule='+"0"N(1)'; message="more than 1 digits"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_sym_b: +"0"N(1) */
  fu12_sym_b = input(strip(_r8), ?? best32.);
  if not missing(_r8) and missing(fu12_sym_b) then do;
    variable="fu12_sym_b"; value=_r8; type="format"; rule='+"0"N(1)'; message="not numeric"; _n_fmt + 1; output _crf_fmt;
  end;
  else if length(scan(strip(_r8), 1, '.')) > 1 then do;
    variable="fu12_sym_b"; value=_r8; type="format"; rule='+"0"N(1)'; message="more than 1 digits"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_sym_c: +"0"N(1) */
  fu12_sym_c = input(strip(_r9), ?? best32.);
  if not missing(_r9) and missing(fu12_sym_c) then do;
    variable="fu12_sym_c"; value=_r9; type="format"; rule='+"0"N(1)'; message="not numeric"; _n_fmt + 1; output _crf_fmt;
  end;
  else if length(scan(strip(_r9), 1, '.')) > 1 then do;
    variable="fu12_sym_c"; value=_r9; type="format"; rule='+"0"N(1)'; message="more than 1 digits"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_sym_d: +"0"N(1) */
  fu12_sym_d = input(strip(_r10), ?? best32.);
  if not missing(_r10) and missing(fu12_sym_d) then do;
    variable="fu12_sym_d"; value=_r10; type="format"; rule='+"0"N(1)'; message="not numeric"; _n_fmt + 1; output _crf_fmt;
  end;
  else if length(scan(strip(_r10), 1, '.')) > 1 then do;
    variable="fu12_sym_d"; value=_r10; type="format"; rule='+"0"N(1)'; message="more than 1 digits"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_hosp: +"0"N(1) */
  fu12_hosp = input(strip(_r11), ?? best32.);
  if not missing(_r11) and missing(fu12_hosp) then do;
    variable="fu12_hosp"; value=_r11; type="format"; rule='+"0"N(1)'; message="not numeric"; _n_fmt + 1; output _crf_fmt;
  end;
  else if length(scan(strip(_r11), 1, '.')) > 1 then do;
    variable="fu12_hosp"; value=_r11; type="format"; rule='+"0"N(1)'; message="more than 1 digits"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_hosp_m: +"0"N(0-2) */
  fu12_hosp_m = input(strip(_r12), ?? best32.);
  if not missing(_r12) and missing(fu12_hosp_m) then do;
    variable="fu12_hosp_m"; value=_r12; type="format"; rule='+"0"N(0-2)'; message="not numeric"; _n_fmt + 1; output _crf_fmt;
  end;
  else if length(scan(strip(_r12), 1, '.')) > 2 then do;
    variable="fu12_hosp_m"; value=_r12; type="format"; rule='+"0"N(0-2)'; message="more than 2 digits"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_hosp_y: +"0"N(0-4) */
  fu12_hosp_y = input(strip(_r13), ?? best32.);
  if not missing(_r13) and missing(fu12_hosp_y) then do;
    variable="fu12_hosp_y"; value=_r13; type="format"; rule='+"0"N(0-4)'; message="not numeric"; _n_fmt + 1; output _crf_fmt;
  end;
  else if length(scan(strip(_r13), 1, '.')) > 4 then do;
    variable="fu12_hosp_y"; value=_r13; type="format"; rule='+"0"N(0-4)'; message="more than 4 digits"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_fall: +"0"N(1) */
  fu12_fall = input(strip(_r14), ?? best32.);
  if not missing(_r14) and missing(fu12_fall) then do;
    variable="fu12_fall"; value=_r14; type="format"; rule='+"0"N(1)'; message="not numeric"; _n_fmt + 1; output _crf_fmt;
  end;
  else if length(scan(strip(_r14), 1, '.')) > 1 then do;
    variable="fu12_fall"; value=_r14; type="format"; rule='+"0"N(1)'; message="more than 1 digits"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_falls_n: +"0"N(0-2) */
  fu12_falls_n = input(strip(_r15), ?? best32.);
  if not missing(_r15) and missing(fu12_falls_n) then do;
    variable="fu12_falls_n"; value=_r15; type="format"; rule='+"0"N(0-2)'; message="not numeric"; _n_fmt + 1; output _crf_fmt;
  end;
  else if length(scan(strip(_r15), 1, '.')) > 2 then do;
    variable="fu12_falls_n"; value=_r15; type="format"; rule='+"0"N(0-2)'; message="more than 2 digits"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_newdx: +"0"N(1) */
  fu12_newdx = input(strip(_r16), ?? best32.);
  if not missing(_r16) and missing(fu12_newdx) then do;
    variable="fu12_newdx"; value=_r16; type="format"; rule='+"0"N(1)'; message="not numeric"; _n_fmt + 1; output _crf_fmt;
  end;
  else if length(scan(strip(_r16), 1, '.')) > 1 then do;
    variable="fu12_newdx"; value=_r16; type="format"; rule='+"0"N(1)'; message="more than 1 digits"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_newdx_txt: -" "X(0-50) */
  fu12_newdx_txt = strip(_r17);
  if length(strip(_r17)) > 50 then do;
    variable="fu12_newdx_txt"; value=_r17; type="format"; rule='-" "X(0-50)'; message="text longer than 50 characters"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_med1: -" "X(0-50) */
  fu12_med1 = strip(_r18);
  if length(strip(_r18)) > 50 then do;
    variable="fu12_med1"; value=_r18; type="format"; rule='-" "X(0-50)'; message="text longer than 50 characters"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_med1_daily: +"0"N(1) */
  fu12_med1_daily = input(strip(_r19), ?? best32.);
  if not missing(_r19) and missing(fu12_med1_daily) then do;
    variable="fu12_med1_daily"; value=_r19; type="format"; rule='+"0"N(1)'; message="not numeric"; _n_fmt + 1; output _crf_fmt;
  end;
  else if length(scan(strip(_r19), 1, '.')) > 1 then do;
    variable="fu12_med1_daily"; value=_r19; type="format"; rule='+"0"N(1)'; message="more than 1 digits"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_med2: -" "X(0-50) */
  fu12_med2 = strip(_r20);
  if length(strip(_r20)) > 50 then do;
    variable="fu12_med2"; value=_r20; type="format"; rule='-" "X(0-50)'; message="text longer than 50 characters"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_med2_daily: +"0"N(1) */
  fu12_med2_daily = input(strip(_r21), ?? best32.);
  if not missing(_r21) and missing(fu12_med2_daily) then do;
    variable="fu12_med2_daily"; value=_r21; type="format"; rule='+"0"N(1)'; message="not numeric"; _n_fmt + 1; output _crf_fmt;
  end;
  else if length(scan(strip(_r21), 1, '.')) > 1 then do;
    variable="fu12_med2_daily"; value=_r21; type="format"; rule='+"0"N(1)'; message="more than 1 digits"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_weight: +"0"N(0-3) */
  fu12_weight = input(strip(_r22), ?? best32.);
  if not missing(_r22) and missing(fu12_weight) then do;
    variable="fu12_weight"; value=_r22; type="format"; rule='+"0"N(0-3)'; message="not numeric"; _n_fmt + 1; output _crf_fmt;
  end;
  else if length(scan(strip(_r22), 1, '.')) > 3 then do;
    variable="fu12_weight"; value=_r22; type="format"; rule='+"0"N(0-3)'; message="more than 3 digits"; _n_fmt + 1; output _crf_fmt;
  end;
  /* fu12_steps: +"0"N(0-5) */
  fu12_steps = input(strip(_r23), ?? best32.);
  if not missing(_r23) and missing(fu12_steps) then do;
    variable="fu12_steps"; value=_r23; type="format"; rule='+"0"N(0-5)'; message="not numeric"; _n_fmt + 1; output _crf_fmt;
  end;
  else if length(scan(strip(_r23), 1, '.')) > 5 then do;
    variable="fu12_steps"; value=_r23; type="format"; rule='+"0"N(0-5)'; message="more than 5 digits"; _n_fmt + 1; output _crf_fmt;
  end;
  /* scan_date: YYMMDD */
  scan_date = input(strip(_r24), ?? yymmdd8.);
  format scan_date yymmdd10.;
  if not missing(_r24) and missing(scan_date) then do;
    variable="scan_date"; value=_r24; type="format"; rule='YYMMDD'; message="not a valid date (YYYYMMDD)"; _n_fmt + 1; output _crf_fmt;
  end;
  /* scan_user: -" "X(12) */
  scan_user = strip(_r25);
  if length(strip(_r25)) > 12 then do;
    variable="scan_user"; value=_r25; type="format"; rule='-" "X(12)'; message="text longer than 12 characters"; _n_fmt + 1; output _crf_fmt;
  end;
  output _crf_typed;
run;

/* 3. Plausibility rules from the Excel sheet */
data &outlib..cleaned(drop=variable value type rule message _n_fmt)
     _crf_rules(keep=id variable value type rule message);
  set _crf_typed;
  length variable $32 value $200 type $6 rule $500 message $200;
  _n_errors = _n_fmt;
  /* id: # >= 1001 and # <= 1999 */
  if not (id >= 1001 and id <= 1999) then do;
    _n_errors = _n_errors + 1; variable="id"; value=strip(vvalue(id)); type="rule";
    rule='id >= 1001 and id <= 1999'; message='ID outside the assigned range 1001-1999'; output _crf_rules;
  end;
  /* fu12_day: # >= 1 and ((fu12_month in (1,3,5,7,8,10,12) and # <= 31) or (fu12_month in (4,6,9,11) and # <= 30) or (fu12_month = 2 and # <= 29)) */
  if not (fu12_day >= 1 and ((fu12_month in (1,3,5,7,8,10,12) and fu12_day <= 31) or (fu12_month in (4,6,9,11) and fu12_day <= 30) or (fu12_month = 2 and fu12_day <= 29))) then do;
    _n_errors = _n_errors + 1; variable="fu12_day"; value=strip(vvalue(fu12_day)); type="rule";
    rule='fu12_day >= 1 and ((fu12_month in (1,3,5,7,8,10,12) and fu12_day <= 31) or (fu12_month in (4,6,9,11) and fu12_day <= 30) or (fu12_month = 2 and fu12_day <= 29))'; message='Day does not exist in this month'; output _crf_rules;
  end;
  /* fu12_month: # >= 1 and # <= 12 */
  if not (fu12_month >= 1 and fu12_month <= 12) then do;
    _n_errors = _n_errors + 1; variable="fu12_month"; value=strip(vvalue(fu12_month)); type="rule";
    rule='fu12_month >= 1 and fu12_month <= 12'; message='Month missing or not between 1 and 12'; output _crf_rules;
  end;
  /* fu12_year: # >= 2024 and # <= year(today()) */
  if not (fu12_year >= 2024 and fu12_year <= year(today())) then do;
    _n_errors = _n_errors + 1; variable="fu12_year"; value=strip(vvalue(fu12_year)); type="rule";
    rule='fu12_year >= 2024 and fu12_year <= year(today())'; message='Year outside the study period'; output _crf_rules;
  end;
  /* fu12_age: # >= 65 and # <= 110 */
  if not (fu12_age >= 65 and fu12_age <= 110) then do;
    _n_errors = _n_errors + 1; variable="fu12_age"; value=strip(vvalue(fu12_age)); type="rule";
    rule='fu12_age >= 65 and fu12_age <= 110'; message='Age outside the inclusion range (65+)'; output _crf_rules;
  end;
  /* fu12_health: # in (1 2 3 4 5 6 7) */
  if not (fu12_health in (1 2 3 4 5 6 7)) then do;
    _n_errors = _n_errors + 1; variable="fu12_health"; value=strip(vvalue(fu12_health)); type="rule";
    rule='fu12_health in (1 2 3 4 5 6 7)'; message='Health rating missing, out of range or several boxes ticked (8)'; output _crf_rules;
  end;
  /* fu12_sym_a: # NOT IN (8 88) */
  if not (fu12_sym_a NOT IN (8 88)) then do;
    _n_errors = _n_errors + 1; variable="fu12_sym_a"; value=strip(vvalue(fu12_sym_a)); type="rule";
    rule='fu12_sym_a NOT IN (8 88)'; message='Several boxes ticked'; output _crf_rules;
  end;
  /* fu12_sym_b: # NOT IN (8 88) */
  if not (fu12_sym_b NOT IN (8 88)) then do;
    _n_errors = _n_errors + 1; variable="fu12_sym_b"; value=strip(vvalue(fu12_sym_b)); type="rule";
    rule='fu12_sym_b NOT IN (8 88)'; message='Several boxes ticked'; output _crf_rules;
  end;
  /* fu12_sym_c: missing(#) or # in (1,2,3,4) */
  if not (missing(fu12_sym_c) or fu12_sym_c in (1,2,3,4)) then do;
    _n_errors = _n_errors + 1; variable="fu12_sym_c"; value=strip(vvalue(fu12_sym_c)); type="rule";
    rule='missing(fu12_sym_c) or fu12_sym_c in (1,2,3,4)'; message='Value outside 1-4 or several boxes ticked'; output _crf_rules;
  end;
  /* fu12_sym_d: missing(#) or # in (1,2,3,4) */
  if not (missing(fu12_sym_d) or fu12_sym_d in (1,2,3,4)) then do;
    _n_errors = _n_errors + 1; variable="fu12_sym_d"; value=strip(vvalue(fu12_sym_d)); type="rule";
    rule='missing(fu12_sym_d) or fu12_sym_d in (1,2,3,4)'; message='Value outside 1-4 or several boxes ticked'; output _crf_rules;
  end;
  /* fu12_hosp: (# = 0 and fu12_hosp_m = . and fu12_hosp_y = .) or # = 1 */
  if not ((fu12_hosp = 0 and fu12_hosp_m = . and fu12_hosp_y = .) or fu12_hosp = 1) then do;
    _n_errors = _n_errors + 1; variable="fu12_hosp"; value=strip(vvalue(fu12_hosp)); type="rule";
    rule='(fu12_hosp = 0 and fu12_hosp_m = . and fu12_hosp_y = .) or fu12_hosp = 1'; message='Hospital stay missing, or ''no'' although a date is given'; output _crf_rules;
  end;
  /* fu12_hosp_m: missing(#) or (# >= 1 and # <= 12 and fu12_hosp_y ~= .) */
  if not (missing(fu12_hosp_m) or (fu12_hosp_m >= 1 and fu12_hosp_m <= 12 and fu12_hosp_y ~= .)) then do;
    _n_errors = _n_errors + 1; variable="fu12_hosp_m"; value=strip(vvalue(fu12_hosp_m)); type="rule";
    rule='missing(fu12_hosp_m) or (fu12_hosp_m >= 1 and fu12_hosp_m <= 12 and fu12_hosp_y ~= .)'; message='Month invalid or year missing'; output _crf_rules;
  end;
  /* fu12_hosp_y: (missing(#) and fu12_hosp in (0 .)) or (fu12_hosp = 1 and # >= 2024 and # <= fu12_year) */
  if not ((missing(fu12_hosp_y) and fu12_hosp in (0 .)) or (fu12_hosp = 1 and fu12_hosp_y >= 2024 and fu12_hosp_y <= fu12_year)) then do;
    _n_errors = _n_errors + 1; variable="fu12_hosp_y"; value=strip(vvalue(fu12_hosp_y)); type="rule";
    rule='(missing(fu12_hosp_y) and fu12_hosp in (0 .)) or (fu12_hosp = 1 and fu12_hosp_y >= 2024 and fu12_hosp_y <= fu12_year)'; message='Year missing although stay = yes, or later than the questionnaire'; output _crf_rules;
  end;
  /* fu12_fall: # in (0 1 2) */
  if not (fu12_fall in (0 1 2)) then do;
    _n_errors = _n_errors + 1; variable="fu12_fall"; value=strip(vvalue(fu12_fall)); type="rule";
    rule='fu12_fall in (0 1 2)'; message='Fall question missing or several boxes ticked'; output _crf_rules;
  end;
  /* fu12_falls_n: (fu12_fall = 1 and # >= 1) or (fu12_fall in (0 2 .) and missing(#)) */
  if not ((fu12_fall = 1 and fu12_falls_n >= 1) or (fu12_fall in (0 2 .) and missing(fu12_falls_n))) then do;
    _n_errors = _n_errors + 1; variable="fu12_falls_n"; value=strip(vvalue(fu12_falls_n)); type="rule";
    rule='(fu12_fall = 1 and fu12_falls_n >= 1) or (fu12_fall in (0 2 .) and missing(fu12_falls_n))'; message='Number of falls does not match the fall question'; output _crf_rules;
  end;
  /* fu12_newdx: # in (0 1) */
  if not (fu12_newdx in (0 1)) then do;
    _n_errors = _n_errors + 1; variable="fu12_newdx"; value=strip(vvalue(fu12_newdx)); type="rule";
    rule='fu12_newdx in (0 1)'; message='New-diagnosis question missing or several boxes ticked'; output _crf_rules;
  end;
  /* fu12_newdx_txt: (fu12_newdx = 1 and not missing(#)) or (fu12_newdx in (0 .) and missing(#)) */
  if not ((fu12_newdx = 1 and not missing(fu12_newdx_txt)) or (fu12_newdx in (0 .) and missing(fu12_newdx_txt))) then do;
    _n_errors = _n_errors + 1; variable="fu12_newdx_txt"; value=strip(vvalue(fu12_newdx_txt)); type="rule";
    rule='(fu12_newdx = 1 and not missing(fu12_newdx_txt)) or (fu12_newdx in (0 .) and missing(fu12_newdx_txt))'; message='Diagnosis text does not match the yes/no answer'; output _crf_rules;
  end;
  /* fu12_med1_daily: # in (0 1 .) and (# ~= 1 or not missing(fu12_med1)) */
  if not (fu12_med1_daily in (0 1 .) and (fu12_med1_daily ~= 1 or not missing(fu12_med1))) then do;
    _n_errors = _n_errors + 1; variable="fu12_med1_daily"; value=strip(vvalue(fu12_med1_daily)); type="rule";
    rule='fu12_med1_daily in (0 1 .) and (fu12_med1_daily ~= 1 or not missing(fu12_med1))'; message='Daily intake ticked but no medication name'; output _crf_rules;
  end;
  /* fu12_med2_daily: # in (0 1 .) and (# ~= 1 or not missing(fu12_med2)) */
  if not (fu12_med2_daily in (0 1 .) and (fu12_med2_daily ~= 1 or not missing(fu12_med2))) then do;
    _n_errors = _n_errors + 1; variable="fu12_med2_daily"; value=strip(vvalue(fu12_med2_daily)); type="rule";
    rule='fu12_med2_daily in (0 1 .) and (fu12_med2_daily ~= 1 or not missing(fu12_med2))'; message='Daily intake ticked but no medication name'; output _crf_rules;
  end;
  /* fu12_weight: missing(#) or (# >= 35 and # <= 200) */
  if not (missing(fu12_weight) or (fu12_weight >= 35 and fu12_weight <= 200)) then do;
    _n_errors = _n_errors + 1; variable="fu12_weight"; value=strip(vvalue(fu12_weight)); type="rule";
    rule='missing(fu12_weight) or (fu12_weight >= 35 and fu12_weight <= 200)'; message='Implausible body weight'; output _crf_rules;
  end;
  /* fu12_steps: missing(#) or # <= 40000 */
  if not (missing(fu12_steps) or fu12_steps <= 40000) then do;
    _n_errors = _n_errors + 1; variable="fu12_steps"; value=strip(vvalue(fu12_steps)); type="rule";
    rule='missing(fu12_steps) or fu12_steps <= 40000'; message='Implausible number of daily steps'; output _crf_rules;
  end;
  /* scan_date: not missing(#) and # >= mdy(fu12_month, fu12_day, fu12_year) */
  if not (not missing(scan_date) and scan_date >= mdy(fu12_month, fu12_day, fu12_year)) then do;
    _n_errors = _n_errors + 1; variable="scan_date"; value=strip(vvalue(scan_date)); type="rule";
    rule='not missing(scan_date) and scan_date >= mdy(fu12_month, fu12_day, fu12_year)'; message='Scan date missing or before the date of completion'; output _crf_rules;
  end;
  /* scan_user: not missing(#) */
  if not (not missing(scan_user)) then do;
    _n_errors = _n_errors + 1; variable="scan_user"; value=strip(vvalue(scan_user)); type="rule";
    rule='not missing(scan_user)'; message='Scanner operator missing'; output _crf_rules;
  end;
  output &outlib..cleaned;
run;

/* 4. Findings table (format + rule) and summary */
data &outlib..findings;
  set _crf_fmt _crf_rules;
run;
proc sort data=&outlib..findings; by id type variable; run;

proc sql;
  create table &outlib..summary as
  select count(*) as records,
         sum(_n_errors = 0) as records_without_findings,
         sum(_n_errors > 0) as records_with_findings,
         calculated records_with_findings / calculated records * 100
           as pct_with_findings format=5.1
  from &outlib..cleaned;
quit;

%if %length(&outdir.) %then %do;
  ods excel file="&outdir./plausibility_report.xlsx" options(sheet_name="summary" frozen_headers="on");
  proc print data=&outlib..summary noobs; run;
  ods excel options(sheet_name="findings" autofilter="all" frozen_headers="on");
  proc print data=&outlib..findings noobs; run;
  ods excel close;
  proc export data=&outlib..cleaned outfile="&outdir./cleaned.csv" dbms=csv replace; run;
%end;

proc datasets lib=work nolist; delete _crf_:; quit;
%mend crf_clean;
