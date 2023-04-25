%
O2001;
G20 G90 G17 G94 G49 G40 G80;
M06 T03;
M01;
G54 G00 X-.5 Y.125;
G43 H03 Z1.0;
M03 S4000;
M08;
G01 Z0.0 F24.;

#10100 = .125 (Cutter Radius);
#10101 = .5 (Corner Radius);
#10102 = 0.0 (Length from call to G65 P9001);

G00 X2.75 Y1.25;
G01 X2.75 Y.875;
G03 X3.125 Y1.25 I0 J.375;
G65 P9001 A[#10100] C[#10100+#10101] V10102.;
G01 X3.125 Y[1.625+#10100+#10101-#10102];

G00 Z.1 M09;
G53 G49 Z0.0 M05;
G53 Y0.0;
M30;
%

%
(Pythagorean Theorem);
(Example: G65 P9001 A[] C[] V[]);
(A = the length of a known side, local var #1);
(C = the length of a known hypotenuse, local var #3);
(V = the var number to store the answer, local var #22);
O9001; 
#[#22] = SQRT[[#3 * #3] - [#1 * #1]];
M99;
%
