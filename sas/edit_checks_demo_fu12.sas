/* ============================================================================
   EDIT-CHECK PROGRAM  -  generated from demo_fu12_rules.xlsx on 2026-11-02
   Do not edit by hand: change the rules sheet and generate the program again.

   Step 1  read the raw scanner export (every field as text, file is never changed)
   Step 2  apply the correction log  -> audit trail (applied / conflict)
   Step 3  convert text to numbers and dates  -> format findings
   Step 4  check the 24 plausibility rules  -> rule findings
   Step 5  save: cleaned data, findings, audit trail, one query file per site
   ============================================================================ */

/* ---- set these three paths, then run the whole program ---------------------- */
%let raw_file        = C:/study/data/raw_export.csv;
%let correction_log  = C:/study/corrections/corrections_log.xlsx;
%let output_folder   = C:/study/output;

/* ---- Step 1: read the raw export. t_ = text exactly as scanned ------------- */
data raw;
  infile "&raw_file." dlm="|" dsd truncover firstobs=2 lrecl=32767;
  length t_id t_site t_fu12_day t_fu12_month t_fu12_year t_fu12_age t_fu12_health
  t_fu12_sym_a t_fu12_sym_b t_fu12_sym_c t_fu12_sym_d t_fu12_hosp t_fu12_hosp_m
  t_fu12_hosp_y t_fu12_fall t_fu12_falls_n t_fu12_newdx t_fu12_newdx_txt t_fu12_med1
  t_fu12_med1_daily t_fu12_med2 t_fu12_med2_daily t_fu12_weight t_fu12_steps t_scan_date
  t_scan_user $200;
  input t_id t_site t_fu12_day t_fu12_month t_fu12_year t_fu12_age t_fu12_health
  t_fu12_sym_a t_fu12_sym_b t_fu12_sym_c t_fu12_sym_d t_fu12_hosp t_fu12_hosp_m
  t_fu12_hosp_y t_fu12_fall t_fu12_falls_n t_fu12_newdx t_fu12_newdx_txt t_fu12_med1
  t_fu12_med1_daily t_fu12_med2 t_fu12_med2_daily t_fu12_weight t_fu12_steps t_scan_date
  t_scan_user ;
run;

/* ---- Step 2: apply the correction log ----------------------------------------
   Every change to the data is a row in the correction log (who, what, when, why).
   A change is applied only if the value in the data still equals old_value;
   otherwise it is marked as conflict and nothing is changed.                      */
proc import datafile="&correction_log." out=log_import dbms=xlsx replace;
  getnames=yes;
run;

data corrections;   /* make every column text, whatever Excel stored */
  set log_import(rename=(id=_id old_value=_old new_value=_new));
  length id old_value new_value $200;
  id = cats(_id);  old_value = cats(_old);  new_value = cats(_new);
  if old_value = "." then old_value = "";
  if new_value = "." then new_value = "";
  variable = lowcase(strip(variable));
  drop _id _old _new;
run;

data raw_corrected(drop=id correction_id variable old_value new_value found_value status rc i)
     audit_trail(keep=correction_id id variable old_value new_value found_value status);
  set raw;
  array field {*} $ t_id--t_scan_user;   /* all fields of the export */
  length correction_id $20 variable $32 old_value new_value found_value $200 status $10 id $200;
  if _n_ = 1 then do;   /* load the log into memory, looked up by participant ID */
    declare hash corr(dataset: "corrections", multidata: "yes");
    corr.defineKey("id");
    corr.defineData("correction_id", "variable", "old_value", "new_value");
    corr.defineDone();
  end;
  id = strip(t_id);
  rc = corr.find();
  do while (rc = 0);   /* every correction for this participant */
    do i = 1 to dim(field);
      if lowcase(vname(field{i})) = cats("t_", variable) then do;
        found_value = field{i};
        if strip(found_value) = strip(old_value) then do; field{i} = new_value; status = "applied"; end;
        else status = "conflict";
        output audit_trail;
      end;
    end;
    rc = corr.find_next();
  end;
  output raw_corrected;
run;

/* ---- Steps 3 and 4: convert and check -------------------------------------- */
data checked(drop=t_: query_id variable value type message rule)
     findings(keep=query_id site id variable value type message rule);
  set raw_corrected;
  length query_id $60 variable $32 value $200 type $6 message $200 rule $500;
  n_findings = 0;

  /* Step 3: text -> number / date. Anything that cannot be read is a finding. */
  id = input(t_id, ?? best32.);
  if t_id ne "" and id = . then do; variable="id"; value=t_id; type="format"; message="not a number"; rule='+"0"N(4)'; link add_finding; end;
  length site $3;  site = strip(t_site);
  if length(strip(t_site)) > 3 then do; variable="site"; value=t_site; type="format"; message="text longer than 3 characters"; rule='-" "X(3)'; link add_finding; end;
  fu12_day = input(t_fu12_day, ?? best32.);
  if t_fu12_day ne "" and fu12_day = . then do; variable="fu12_day"; value=t_fu12_day; type="format"; message="not a number"; rule='+"0"N(0-2)'; link add_finding; end;
  fu12_month = input(t_fu12_month, ?? best32.);
  if t_fu12_month ne "" and fu12_month = . then do; variable="fu12_month"; value=t_fu12_month; type="format"; message="not a number"; rule='+"0"N(0-2)'; link add_finding; end;
  fu12_year = input(t_fu12_year, ?? best32.);
  if t_fu12_year ne "" and fu12_year = . then do; variable="fu12_year"; value=t_fu12_year; type="format"; message="not a number"; rule='+"0"N(0-4)'; link add_finding; end;
  fu12_age = input(t_fu12_age, ?? best32.);
  if t_fu12_age ne "" and fu12_age = . then do; variable="fu12_age"; value=t_fu12_age; type="format"; message="not a number"; rule='+"0"N(0-3)'; link add_finding; end;
  fu12_health = input(t_fu12_health, ?? best32.);
  if t_fu12_health ne "" and fu12_health = . then do; variable="fu12_health"; value=t_fu12_health; type="format"; message="not a number"; rule='+"0"N(1)'; link add_finding; end;
  fu12_sym_a = input(t_fu12_sym_a, ?? best32.);
  if t_fu12_sym_a ne "" and fu12_sym_a = . then do; variable="fu12_sym_a"; value=t_fu12_sym_a; type="format"; message="not a number"; rule='+"0"N(1)'; link add_finding; end;
  fu12_sym_b = input(t_fu12_sym_b, ?? best32.);
  if t_fu12_sym_b ne "" and fu12_sym_b = . then do; variable="fu12_sym_b"; value=t_fu12_sym_b; type="format"; message="not a number"; rule='+"0"N(1)'; link add_finding; end;
  fu12_sym_c = input(t_fu12_sym_c, ?? best32.);
  if t_fu12_sym_c ne "" and fu12_sym_c = . then do; variable="fu12_sym_c"; value=t_fu12_sym_c; type="format"; message="not a number"; rule='+"0"N(1)'; link add_finding; end;
  fu12_sym_d = input(t_fu12_sym_d, ?? best32.);
  if t_fu12_sym_d ne "" and fu12_sym_d = . then do; variable="fu12_sym_d"; value=t_fu12_sym_d; type="format"; message="not a number"; rule='+"0"N(1)'; link add_finding; end;
  fu12_hosp = input(t_fu12_hosp, ?? best32.);
  if t_fu12_hosp ne "" and fu12_hosp = . then do; variable="fu12_hosp"; value=t_fu12_hosp; type="format"; message="not a number"; rule='+"0"N(1)'; link add_finding; end;
  fu12_hosp_m = input(t_fu12_hosp_m, ?? best32.);
  if t_fu12_hosp_m ne "" and fu12_hosp_m = . then do; variable="fu12_hosp_m"; value=t_fu12_hosp_m; type="format"; message="not a number"; rule='+"0"N(0-2)'; link add_finding; end;
  fu12_hosp_y = input(t_fu12_hosp_y, ?? best32.);
  if t_fu12_hosp_y ne "" and fu12_hosp_y = . then do; variable="fu12_hosp_y"; value=t_fu12_hosp_y; type="format"; message="not a number"; rule='+"0"N(0-4)'; link add_finding; end;
  fu12_fall = input(t_fu12_fall, ?? best32.);
  if t_fu12_fall ne "" and fu12_fall = . then do; variable="fu12_fall"; value=t_fu12_fall; type="format"; message="not a number"; rule='+"0"N(1)'; link add_finding; end;
  fu12_falls_n = input(t_fu12_falls_n, ?? best32.);
  if t_fu12_falls_n ne "" and fu12_falls_n = . then do; variable="fu12_falls_n"; value=t_fu12_falls_n; type="format"; message="not a number"; rule='+"0"N(0-2)'; link add_finding; end;
  fu12_newdx = input(t_fu12_newdx, ?? best32.);
  if t_fu12_newdx ne "" and fu12_newdx = . then do; variable="fu12_newdx"; value=t_fu12_newdx; type="format"; message="not a number"; rule='+"0"N(1)'; link add_finding; end;
  length fu12_newdx_txt $50;  fu12_newdx_txt = strip(t_fu12_newdx_txt);
  if length(strip(t_fu12_newdx_txt)) > 50 then do; variable="fu12_newdx_txt"; value=t_fu12_newdx_txt; type="format"; message="text longer than 50 characters"; rule='-" "X(0-50)'; link add_finding; end;
  length fu12_med1 $50;  fu12_med1 = strip(t_fu12_med1);
  if length(strip(t_fu12_med1)) > 50 then do; variable="fu12_med1"; value=t_fu12_med1; type="format"; message="text longer than 50 characters"; rule='-" "X(0-50)'; link add_finding; end;
  fu12_med1_daily = input(t_fu12_med1_daily, ?? best32.);
  if t_fu12_med1_daily ne "" and fu12_med1_daily = . then do; variable="fu12_med1_daily"; value=t_fu12_med1_daily; type="format"; message="not a number"; rule='+"0"N(1)'; link add_finding; end;
  length fu12_med2 $50;  fu12_med2 = strip(t_fu12_med2);
  if length(strip(t_fu12_med2)) > 50 then do; variable="fu12_med2"; value=t_fu12_med2; type="format"; message="text longer than 50 characters"; rule='-" "X(0-50)'; link add_finding; end;
  fu12_med2_daily = input(t_fu12_med2_daily, ?? best32.);
  if t_fu12_med2_daily ne "" and fu12_med2_daily = . then do; variable="fu12_med2_daily"; value=t_fu12_med2_daily; type="format"; message="not a number"; rule='+"0"N(1)'; link add_finding; end;
  fu12_weight = input(t_fu12_weight, ?? best32.);
  if t_fu12_weight ne "" and fu12_weight = . then do; variable="fu12_weight"; value=t_fu12_weight; type="format"; message="not a number"; rule='+"0"N(0-3)'; link add_finding; end;
  fu12_steps = input(t_fu12_steps, ?? best32.);
  if t_fu12_steps ne "" and fu12_steps = . then do; variable="fu12_steps"; value=t_fu12_steps; type="format"; message="not a number"; rule='+"0"N(0-5)'; link add_finding; end;
  scan_date = input(t_scan_date, ?? yymmdd8.);  format scan_date yymmdd10.;
  if t_scan_date ne "" and scan_date = . then do; variable="scan_date"; value=t_scan_date; type="format"; message="not a valid date (YYYYMMDD)"; rule='YYMMDD'; link add_finding; end;
  length scan_user $12;  scan_user = strip(t_scan_user);
  if length(strip(t_scan_user)) > 12 then do; variable="scan_user"; value=t_scan_user; type="format"; message="text longer than 12 characters"; rule='-" "X(12)'; link add_finding; end;

  /* Step 4: plausibility rules from the rules sheet. A rule describes a GOOD value. */

  /* id: Participant ID */
  if not (id >= 1001 and id <= 1999) then do;
    variable="id"; value=vvalue(id); type="rule";
    message='ID outside the assigned range 1001-1999';
    rule='id >= 1001 and id <= 1999';
    link add_finding;
  end;

  /* site: Study site (clinic) */
  if not (site in ("S01","S02","S03","S04")) then do;
    variable="site"; value=vvalue(site); type="rule";
    message='Unknown study site';
    rule='site in ("S01","S02","S03","S04")';
    link add_finding;
  end;

  /* fu12_day: Q0 Date of completion: day */
  if not (fu12_day >= 1 and ((fu12_month in (1,3,5,7,8,10,12) and fu12_day <= 31) or (fu12_month in (4,6,9,11) and fu12_day <= 30) or (fu12_month = 2 and fu12_day <= 29))) then do;
    variable="fu12_day"; value=vvalue(fu12_day); type="rule";
    message='Day does not exist in this month';
    rule='fu12_day >= 1 and ((fu12_month in (1,3,5,7,8,10,12) and fu12_day <= 31) or (fu12_month in (4,6,9,11) and fu12_day <= 30) or (fu12_month = 2 and fu12_day <= 29))';
    link add_finding;
  end;

  /* fu12_month: Q0 Date of completion: month */
  if not (fu12_month >= 1 and fu12_month <= 12) then do;
    variable="fu12_month"; value=vvalue(fu12_month); type="rule";
    message='Month missing or not between 1 and 12';
    rule='fu12_month >= 1 and fu12_month <= 12';
    link add_finding;
  end;

  /* fu12_year: Q0 Date of completion: year */
  if not (fu12_year >= 2024 and fu12_year <= year(today())) then do;
    variable="fu12_year"; value=vvalue(fu12_year); type="rule";
    message='Year outside the study period';
    rule='fu12_year >= 2024 and fu12_year <= year(today())';
    link add_finding;
  end;

  /* fu12_age: Q1 Age in years */
  if not (fu12_age >= 65 and fu12_age <= 110) then do;
    variable="fu12_age"; value=vvalue(fu12_age); type="rule";
    message='Age outside the inclusion range (65+)';
    rule='fu12_age >= 65 and fu12_age <= 110';
    link add_finding;
  end;

  /* fu12_health: Q2 Overall health today */
  if not (fu12_health in (1 2 3 4 5 6 7)) then do;
    variable="fu12_health"; value=vvalue(fu12_health); type="rule";
    message='Health rating missing, out of range or several boxes ticked (8)';
    rule='fu12_health in (1 2 3 4 5 6 7)';
    link add_finding;
  end;

  /* fu12_sym_a: Q3a Tiredness last week */
  if not (fu12_sym_a NOT IN (8 88)) then do;
    variable="fu12_sym_a"; value=vvalue(fu12_sym_a); type="rule";
    message='Several boxes ticked';
    rule='fu12_sym_a NOT IN (8 88)';
    link add_finding;
  end;

  /* fu12_sym_b: Q3b Pain last week */
  if not (fu12_sym_b NOT IN (8 88)) then do;
    variable="fu12_sym_b"; value=vvalue(fu12_sym_b); type="rule";
    message='Several boxes ticked';
    rule='fu12_sym_b NOT IN (8 88)';
    link add_finding;
  end;

  /* fu12_sym_c: Q3c Shortness of breath last week */
  if not (missing(fu12_sym_c) or fu12_sym_c in (1,2,3,4)) then do;
    variable="fu12_sym_c"; value=vvalue(fu12_sym_c); type="rule";
    message='Value outside 1-4 or several boxes ticked';
    rule='missing(fu12_sym_c) or fu12_sym_c in (1,2,3,4)';
    link add_finding;
  end;

  /* fu12_sym_d: Q3d Trouble sleeping last week */
  if not (missing(fu12_sym_d) or fu12_sym_d in (1,2,3,4)) then do;
    variable="fu12_sym_d"; value=vvalue(fu12_sym_d); type="rule";
    message='Value outside 1-4 or several boxes ticked';
    rule='missing(fu12_sym_d) or fu12_sym_d in (1,2,3,4)';
    link add_finding;
  end;

  /* fu12_hosp: Q4 Hospital stay since last visit */
  if not ((fu12_hosp = 0 and fu12_hosp_m = . and fu12_hosp_y = .) or fu12_hosp = 1) then do;
    variable="fu12_hosp"; value=vvalue(fu12_hosp); type="rule";
    message='Hospital stay missing, or ''no'' although a date is given';
    rule='(fu12_hosp = 0 and fu12_hosp_m = . and fu12_hosp_y = .) or fu12_hosp = 1';
    link add_finding;
  end;

  /* fu12_hosp_m: Q4a Hospital stay: month */
  if not (missing(fu12_hosp_m) or (fu12_hosp_m >= 1 and fu12_hosp_m <= 12 and fu12_hosp_y ~= .)) then do;
    variable="fu12_hosp_m"; value=vvalue(fu12_hosp_m); type="rule";
    message='Month invalid or year missing';
    rule='missing(fu12_hosp_m) or (fu12_hosp_m >= 1 and fu12_hosp_m <= 12 and fu12_hosp_y ~= .)';
    link add_finding;
  end;

  /* fu12_hosp_y: Q4b Hospital stay: year */
  if not ((missing(fu12_hosp_y) and fu12_hosp in (0 .)) or (fu12_hosp = 1 and fu12_hosp_y >= 2024 and fu12_hosp_y <= fu12_year)) then do;
    variable="fu12_hosp_y"; value=vvalue(fu12_hosp_y); type="rule";
    message='Year missing although stay = yes, or later than the questionnaire';
    rule='(missing(fu12_hosp_y) and fu12_hosp in (0 .)) or (fu12_hosp = 1 and fu12_hosp_y >= 2024 and fu12_hosp_y <= fu12_year)';
    link add_finding;
  end;

  /* fu12_fall: Q5 Fall in the last 12 months */
  if not (fu12_fall in (0 1 2)) then do;
    variable="fu12_fall"; value=vvalue(fu12_fall); type="rule";
    message='Fall question missing or several boxes ticked';
    rule='fu12_fall in (0 1 2)';
    link add_finding;
  end;

  /* fu12_falls_n: Q5a Number of falls */
  if not ((fu12_fall = 1 and fu12_falls_n >= 1) or (fu12_fall in (0 2 .) and missing(fu12_falls_n))) then do;
    variable="fu12_falls_n"; value=vvalue(fu12_falls_n); type="rule";
    message='Number of falls does not match the fall question';
    rule='(fu12_fall = 1 and fu12_falls_n >= 1) or (fu12_fall in (0 2 .) and missing(fu12_falls_n))';
    link add_finding;
  end;

  /* fu12_newdx: Q6 New diagnosis since last visit */
  if not (fu12_newdx in (0 1)) then do;
    variable="fu12_newdx"; value=vvalue(fu12_newdx); type="rule";
    message='New-diagnosis question missing or several boxes ticked';
    rule='fu12_newdx in (0 1)';
    link add_finding;
  end;

  /* fu12_newdx_txt: Q6a Which diagnosis */
  if not ((fu12_newdx = 1 and not missing(fu12_newdx_txt)) or (fu12_newdx in (0 .) and missing(fu12_newdx_txt))) then do;
    variable="fu12_newdx_txt"; value=vvalue(fu12_newdx_txt); type="rule";
    message='Diagnosis text does not match the yes/no answer';
    rule='(fu12_newdx = 1 and not missing(fu12_newdx_txt)) or (fu12_newdx in (0 .) and missing(fu12_newdx_txt))';
    link add_finding;
  end;

  /* fu12_med1_daily: Q7 Medication 1: taken daily */
  if not (fu12_med1_daily in (0 1 .) and (fu12_med1_daily ~= 1 or not missing(fu12_med1))) then do;
    variable="fu12_med1_daily"; value=vvalue(fu12_med1_daily); type="rule";
    message='Daily intake ticked but no medication name';
    rule='fu12_med1_daily in (0 1 .) and (fu12_med1_daily ~= 1 or not missing(fu12_med1))';
    link add_finding;
  end;

  /* fu12_med2_daily: Q7 Medication 2: taken daily */
  if not (fu12_med2_daily in (0 1 .) and (fu12_med2_daily ~= 1 or not missing(fu12_med2))) then do;
    variable="fu12_med2_daily"; value=vvalue(fu12_med2_daily); type="rule";
    message='Daily intake ticked but no medication name';
    rule='fu12_med2_daily in (0 1 .) and (fu12_med2_daily ~= 1 or not missing(fu12_med2))';
    link add_finding;
  end;

  /* fu12_weight: Q8 Body weight (kg) */
  if not (missing(fu12_weight) or (fu12_weight >= 35 and fu12_weight <= 200)) then do;
    variable="fu12_weight"; value=vvalue(fu12_weight); type="rule";
    message='Implausible body weight';
    rule='missing(fu12_weight) or (fu12_weight >= 35 and fu12_weight <= 200)';
    link add_finding;
  end;

  /* fu12_steps: Q9 Average steps per day */
  if not (missing(fu12_steps) or fu12_steps <= 40000) then do;
    variable="fu12_steps"; value=vvalue(fu12_steps); type="rule";
    message='Implausible number of daily steps';
    rule='missing(fu12_steps) or fu12_steps <= 40000';
    link add_finding;
  end;

  /* scan_date: Scanner: date of scan */
  if not (not missing(scan_date) and scan_date >= mdy(fu12_month, fu12_day, fu12_year)) then do;
    variable="scan_date"; value=vvalue(scan_date); type="rule";
    message='Scan date missing or before the date of completion';
    rule='not missing(scan_date) and scan_date >= mdy(fu12_month, fu12_day, fu12_year)';
    link add_finding;
  end;

  /* scan_user: Scanner: operator */
  if not (not missing(scan_user)) then do;
    variable="scan_user"; value=vvalue(scan_user); type="rule";
    message='Scanner operator missing';
    rule='not missing(scan_user)';
    link add_finding;
  end;

  output checked;
  return;

add_finding:   /* one finding = one query to the site */
  query_id = cats("Q-", id, "-", variable);
  n_findings = n_findings + 1;
  output findings;
  return;
run;

/* ---- Step 5: save results ----------------------------------------------------- */
proc sort data=findings; by site id variable; run;

proc export data=checked     outfile="&output_folder./cleaned.csv"     dbms=csv replace; run;
proc export data=findings    outfile="&output_folder./findings.csv"    dbms=csv replace; run;
proc export data=audit_trail outfile="&output_folder./audit_trail.csv" dbms=csv replace; run;

title 'Summary';
proc sql;
  select count(*)              as records,
         sum(n_findings = 0)   as records_without_findings,
         sum(n_findings > 0)   as records_with_findings
  from checked;
  select status, count(*) as corrections from audit_trail group by status;
quit;
title;

/* One Excel file per site with its queries. Sites fill in the yellow columns. */
data queries;
  set findings;
  length correct_value site_comment answered_by $100;
  call missing(correct_value, site_comment, answered_by);
run;

%macro query_files;
  proc sql noprint; select distinct site into :site_list separated by ' ' from queries; quit;
  %do i = 1 %to %sysfunc(countw(&site_list.));
    %let s = %scan(&site_list., &i.);
    ods excel file="&output_folder./queries_&s..xlsx"
              options(sheet_name="queries" autofilter="all" frozen_headers="on");
    proc print data=queries noobs label; where site = "&s.";
      var query_id id variable value message;
      var correct_value site_comment answered_by / style(data)=[background=lightyellow];
      label query_id='Query ID' id='Participant ID' variable='Field' value='Current value (have)'
            message='Problem (why)' correct_value='Correct value (want)' site_comment='Comment / source'
            answered_by='Answered by / date';
    run;
    ods excel close;
  %end;
%mend query_files;
%query_files
