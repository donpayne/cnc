%
O1002 (Cut Something Bitch!);
G91 G01 Z-.08 (Incremental Depth for Each Pass)
G90 (Back to Absolute Position);
G00 X-.5 Y.125;
G01 X.625 Y.125;
G01 X.625 Y0.0;
G03 X1.375 Y0.0 I.375 J0.0;
G01 X1.375 Y.125;
G01 X1.875 Y.125;
G01 X1.875 Y0.0;
G03 X2.375 Y0.0 I.25 J0.0;
G01 X2.375 Y.125;
G01 X2.875 Y.125;
G01 X2.875 Y0.0;
G03 X3.125 Y0.0 I.125 J0.0;
G01 X3.125 Y.125;
G01 X3.625 Y.125;
G01 X3.625 Y0.0;
G01 X3.625 Y.125;
G01 X3.875 Y.125;
G02 X4.125 Y-.125 I0.0 J-.25;
G01 X4.125 Y-1.125;
G01 X3.1353 Y-1.125;
G01 X3.1353 Y-1.;
G01 X2.8764 Y-1.625;
G01 X1.4463 Y-1.625;
G01 X1.4463 Y-1.5;
G01 X1.0707 Y-2.125;
G01 X.625 Y-2.125;
G02 X.125 Y-1.625 I0.0 J.5;
G01 X.125 Y-1.1768;
G01 X.25 Y-1.1768;
G01 X-.125 Y-.8018;
G01 X-.125 Y-.25;
G02 X.25 Y.125 I.375 J0.0;
G00 X-.5 Y.125;
M99 (Return To M98);
%