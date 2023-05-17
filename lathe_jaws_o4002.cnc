%
Z4.
$AddRegPart 1 X3. Y2.01
O4002 (Lathe Jaws - Side 2);
(Don Payne);
(5/10/2023);5
(Haas Mini Mill);
(G54 X0 Y0 Top Left Corner of Part);
(Z0 Top of Part);
(Tools: T02 2" Facemill, 4 Flute, 1.5" LOC, 2" Offset H#);
(Tools: T04 1/2" Endmill, Square, 3 Flute, 1.75" LOC, 4" Offset H#);
(Tools: T05 1/8" Endmill, Square, 3 Flute, 1" LOC, 1" Offset H#);
G17 (XY Plane Selection);
G20 (Inches);
G94 (Feet Per Minute);
G49 (Cancel G43/G44/G143);
G40 (Cancel Cutter Compensation);
G80 (Cancel Canned Cycle);
G91 G28 Z0. (Z-Home); 
G91 G28 X0. Y0. (XY-Home); 
M1 (Spindle Stop);

(----------Facemill Operation----------);
N10 M6 T2 (2" Facemill);
G90 (Absolute Position);
G54 G0 X-1.2 Y-.5 (Coordinate System);
G43 H2 M3 S400 (Tool Length Compensation);
M8 (Collant On); 
G0 Z.1 F2.4;

(Cut to depth of Z-.25);
G1 Z-.05 (Cut Z-.05 per pass);
X4.2 (Travel part width + 1.2");
Z-.1;
X-1.2;
Z-.15;
X4.2;
Z-.2;
X-1.2;
Z-.25;
X4.2;

G0 Z.1 (Clear Part);
M9 (Collant Off);
G91 G28 Z0. M5 (Z-Home, Spindle Off); 
G91 G28 X0. Y0. (XY-Home); 
M1 (Spindle Stop);

(----------Channel Mill Operation----------);
N20 M6 T9 (3/8" Endmill);
G90 (Absolute Position);
G54 G0 X-.375 Y-.495 (Coordinate System);
G43 H9 M3 S4000 (Tool Length Compensation);
M8 (Collant On); 
G0 Z.1 F24.;

(Cut to depth of Z-.425);
G1 Z-.3 (Cut Z-.05 per pass);
X3.3875 (Travel part width + .3875");
Z-.35;
X-.375;
Z-.4;
X3.3875;
Z-.425;
X-.375;
(Cut to width of .474 on centerline);
Y-.4505 (Rough side pass);
X3.3875;
Y-.5395 (Rough side pass);
X-.375;
Y-.4455 (Finish side pass);
X3.3875;
Y-.5445 (Finish side pass);
X-.375;

G0 Z.1 (Clear Part);
M9 (Collant Off);
G91 G28 Z0. M5 (Z-Home, Spindle Off); 
G91 G28 X0. Y0. (XY-Home); 
M1 (Spindle Stop);

(----------Serration Cut Operation----------);
N20 M6 T8 (Engraving Tool);
G90 (Absolute Position);
G54 G0 X.0295 Y.1875 (Coordinate System);
G43 H8 M3 S4000 (Tool Length Compensation);
M8 (Collant On); 
G0 Z.1 F24.;

G1 Z-.3;
M97 P300 L26 (Zigzag pattern in .118 steps);

G0 Z.1 (Clear Part);
M9 (Collant Off);
G91 G28 Z0. M5 (Z-Home, Spindle Off); 
G91 G28 X0. Y0. (XY-Home); 
M1 (Spindle Stop);

(----------Shutdown Operation----------);
N200 M9; (Collant Off);
G53 G49 M5; (Spindle Off);
M30;

(----------SUBPROGRAM----------);
N300 (Zigzag function);
G91;
(Starting at X.0295 Y.1875);
G1 Y-1.365 (Width of part + .375);
X.059 (Width of serration);
Y1.365;
X.059;
G90;
M99 (RETURN TO MAIN PROGRAM);
%
