%
O3001 (Turners Cube);
(Don Payne);
(4/28/2023);
(Haas Mini Mill);
(G54 X0 Y0 Top Left Corner of Part);
(Z0 Top of Part);
(Tools: T02 2" Facemill, 4 Flute, 1.5" LOC, 2" Offset H#);
(Tools: T04 1/2" Endmill, Square, 3 Flute, 1.75" LOC, 4" Offset H#);
(Tools: T05 1/8" Endmill, Square, 3 Flute, 1" LOC, 1" Offset H#);
G20 (Inches);
G90 (Absolute Position);
G17 (XY Plane Selection);
G94 (Feet Per Minute);
G49 (Cancel G43/G44/G143);
G40 (Cancel Cutter Compensation);
G80 (Cancel Canned Cycle);
M06 T02 (2" Facemill);
M01 (Optional Program Stop);
G54 G00 X-.5 Y.125 (Coordinate System);
G43 H02 Z2.0 (Tool Length Compensation);
M03 S4000 (Spindle Forward Command);
M08 (Collant On); 
G01 Z0.0 F18.;

(Face Top);
M98 P3002 L2; 
M01 (Optional Program Stop);

(Face Front Side);
M98 P3002 L; 
M01 (Optional Program Stop);

O3002 (Facing);
#10110 = -.125 (Depth per pass);
G01;
X-1.5 Y1;
X-1.5 Y-.5
Z[#10110];
X1.5 Y-.5
M17; 



G00 Z.1 M09;
G53 G49 Z0.0 M05;
G53 Y0.0;
M30;
%



