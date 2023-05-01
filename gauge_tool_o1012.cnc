%
O1012 (Cut Something Bitch!);
G00 X-.25 Y0;
G91 G01 Z-.08 (Incremental Depth for Each Pass)
G90 (Back to Absolute Position);
G41 (Turn on Cutter Comp, Clockwise Outer);
G01 X.5 Y0;
G03 X[1. + .5] Y0 I.5 J0;
G01 X1.75 Y0;
G03 X[2.125 + .375] Y0 I.375 J0;
G01 X2.75 Y0;
G03 X[3. + .25] Y0 I.25 J0;
G01 X3.5 Y0;
G03 X[3.625 + .125] Y0 I.125 J0;
G01 X3.875 Y0;
G02 X4. Y-.125 I0 J-.125;
G01 X4. Y-1.;
(Cut Arc with an 112.5 deg angle);
G01 X[3.1353 + .125] Y-1.;
G03 X[3.1353 - [COS[112.5 - 90] * .125]] Y[-1. + [SIN[112.5 - 90] * .125]] I-.125 J0;
G01 X2.7929 Y-1.5;
(Cut Arc with an 121 deg angle);
G01 X[1.4463 + .125] Y-1.5;
G03 X[1.4463 - [COS[121 - 90] * .125]] Y[-1.5 + [SIN[121 - 90] * .125]] I-.125 J0;
G01 X1. Y-2.;
G01 X.625 Y-2.;
G02 X.25 Y-1.625 I0 J.375;
(Cut Arc with an 135 deg angle);
G01 X.25 Y[-1.1768 - .125];
G03 X[.25 + [SIN[135 - 90] * .125]] Y[-1.1768 + [COS[135 - 90] * .125]] I0 J.125;
G01 X0 Y-.75;
G01 X0 Y-.25;
G02 X.25 Y0 I.25 J0;
G00 X-.25 Y0;
G40 (Turn off Cutter Comp);
M99 (Return To Main);
%
