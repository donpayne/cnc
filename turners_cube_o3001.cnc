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

(Face Top);
N101 M01 (Optional Program Stop);
M06 T2 (2" Facemill);
G54 G00 X-1.2 Y-.5 (Coordinate System);
G43 H2 (Tool Length Compensation);
M03 S2000 (Spindle Forward Command);
M08 (Collant On); 
G00 Z.1 F16.;
G01 Z0;
X2.2;
G00 Z.1;
M09 (Collant Off);
M05 (Spindle Stop);

(Mill Sides);
N102 M01 (Optional Program Stop);
M06 T4 (1/2" Endmill);
G54 G00 X-.5 Y0 (Coordinate System);
G43 H4 (Tool Length Compensation);
M03 S4000 (Spindle Forward Command);
M08 (Collant On); 
G00 Z.1 F24.;
G01 Z-.875;

(Rough Pass);
G41 (Radius Compensation Left Side);
X-.5 Y-.0475;
X.0475 Y-.0475;
X.9525 Y-.0475;
X.9525 Y-.9525;
X.0475 Y-.9525;
X.0475 Y.1;

(Finish Pass);
G41 (Radius Compensation Left Side);
X-.5 Y-.0625;
X.0625 Y-.0625;
X.9375 Y-.0625;
X.9375 Y-.9375;
X.0625 Y-.9375;
X.0625 Y.1;
G40 (Radius Compensation Off);

(Mill Inscribed Circle);
N103 M01 (Optional Program Stop);
M06 T5 (1/8" Endmill);
G54 G00 X.5 Y-.1875 (Coordinate System);
G43 H5 (Tool Length Compensation);
M03 S4000 (Spindle Forward Command);
M08 (Collant On); 
G00 Z.1 F24.;

(Rough Pass);
G01 Z0;
X.5 Y-.2;
G02 X.5 Y-.2 I0 J-.3;
Z-.03 I0 J-.3;
Z-.06 I0 J-.3;
Z-.09 I0 J-.3;
Z-.12 I0 J-.3;
Z-.15 I0 J-.3;
Z-.175 I0 J-.3;
(Inner Finish Pass);
G01 X.5 Y-.2125;
G02 X.5 Y-.2125 I0 J-.2875;
(Outer Finish Pass);
G01 X.5 Y-.1875;
G02 X.5 Y-.1875 I0 J-.3125;

(Shutdown);
N200 G01 Z.1 M09; (Retract, Collant Off);
G53 G49 M05; (Spindle Off);
M30;
%



