%
O2001 (Advanced Arcs);
(Don Payne);
(4/28/2023);
(Haas Mini Mill);
(G54 X0 Y0 Top Left Corner of Part);
(Z0 Top of Part);
G20 (Inches);
G90 (Absolute Position);
G17 (XY Plane Selection);
G94 (Feet Per Minute);
G49 (Cancel G43/G44/G143);
G40 (Cancel Cutter Compensation);
G80 (Cancel Canned Cycle);
M06 T03;
M01;
G54 G00 X-.5 Y.125;
G43 H03 Z1.0;
M03 S4000;
M08;
G01 Z0.0 F24.;

:(Solve for B using the Pythagorean Theorem)
#10100 = 0.0;
G65 P9001 A.125 C.625 V10100.;

G00 X2.75 Y1.25;
G01 X2.75 Y.875;
G03 X3.125 Y1.25 I0 J.375;
G01 X3.125 Y[1.625 + [.625 - #10100]];
G02 X[2.625 + [.625 - #10100]] Y2.125 I.125 J[#10100];
G01 X1.25 Y2.125;
G03 X.875 Y1.75 I0 J-.375;
G01 X.875 Y[1.375 - [.625 - #10100]];
G02 X[1.375 - [.625 - #10100]] Y.875 I-.125 J[-#10100];
G01 X2.75 Y.875;

G00 Z.1 M09;
G53 G49 Z0.0 M05;
G53 Y0.0;
M30;
%
