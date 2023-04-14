%
O1001 (Gauge Project);
(Don Payne);
(4/14/2023);
(Haas Mini Mill);
(G54 X0 Y0 Top Left Corner of Part);
(Z0 Top of Part);
(Tools: T02);
G20 (Inches);
G90 (Absolute Position);
G17 (XY Plane Selection);
G94 (Feet Per Minute);
G49 (Cancel G43/G44/G143);
G40 (Cancel Cutter Compensation);
G80 (Cancel Canned Cycle);
M06 T02 (T02 1/4" Carbide Endmill, 3 Flute, 3/8" LOC);
M01 (Optional Program Stop);
G54 G00 X0 Y0 (Coordinate System);
G43 H01 Z1.0 (Tool Length Compensation);
M03 S1500 (Spindle Forward Command);
M08 (Collant On);
G00 Z.1; 
G01 Z-.008 F10.;
;
;
;
M98 P1002 L3 (Run subroutine 3 times);
;
G00 Z.1 M09 (Rapid Retract, Collant Off);
G53 G49 Z0 M05 (Z Home, Spindle Off);
G53 Y0 (Y Home);
M30 (End Program);
;
;
;
(Cut Something Bitch!);
O1002 (XY Plane Tool Path);
G00 X-.25 Y.125;
G01 X.625 Y.125;
G01 X.625 Y0;
G03 X1.375 Y0 I.375 J0;
G01 X1.375 Y.125;
G01 X1.875 Y.125;
G01 X1.875 Y0;
G03 X2.375 Y0 I.25 J0;
G01 X2.375 Y.125;
G01 X2.875 Y.125;
G01 X2.875 Y0;
G03 X3.125 Y0 I.125 J0;
G01 X3.125 Y.125;
G01 X3.625 Y.125;
G01 X3.625 Y0;
G01 X3.625 Y.125;
G01 X3.875 Y.125;
G02 X4.125 Y-.125 I0 J-.25;
G01 X4.125 Y-1.125;
G01 X3.1353 Y-1.125;
G01 X3.1353 Y-1;
G01 X2.8764 Y-1.625;
G01 X1.4463 Y-1.625;
G01 X1.4463 Y-1.5;
G01 X1.0707 Y-2.125;
G01 X.625 Y-2.125;
G02 X.125 Y-1.625 I0 J.5;
G01 X.125 Y-1.1768;
G01 X.25 Y-1.1768;
G01 X-.125 Y-.8018;
G01 X-.125 Y-.25;
G02 X.25 Y.125 I.375 J0;
G00 X-.25 Y.125;
M99 (Return to Top);
%
