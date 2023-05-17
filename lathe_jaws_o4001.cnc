%
Z4.
$AddRegPart 1 X2.925 Y2.005
O4001 (Lathe Jaws);
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
G43 H2 M3 S400 (Tool Length Compensation, Spindle On);
M8 (Collant On); 
G0 Z.1;
G1 Z0. F2.4;

X4.325 (Add half the cutter diameter and .2");

G0 Z.1 (Clear Part);
M9 (Collant Off);
G91 G28 Z0. M5 (Z-Home, Spindle Off); 
G91 G28 X0. Y0. (XY-Home); 
M1 (Spindle Stop);

(----------Sidemill Operation----------);
N20 M6 T3 (1/2" Endmill);
G90 (Absolute Position);
G54 G0 X-.5 Y0. (Coordinate System);
G43 H3 M3 S4000 (Tool Length Compensation, Spindle On);
M8 (Collant On); 
G0 Z.1;
G1 Z-1.75 F24.;

G41 (Rough Pass);
X-.5 Y0.005
X2.786;
X3.005 Y-.38;
Y-.61;
X2.786 Y-.995;
X-.005;
Y.45;

(Finish Pass);
X-.5 Y0.
X2.781;
X3. Y-.38;
Y-.61;
X2.781 Y-.99;
X0.;
Y.45;
G40;

G0 Z.1;
M9 (Collant Off);
G91 G28 Z0. M5 (Z-Home, Spindle Off); 
G91 G28 X0. Y0. (XY-Home); 
M1 (Spindle Stop);

(----------Spot Drill Operation----------);
N30 M6 T4 (Spot Drill);
G90 (Absolute Position);
G54 G0 X.562 Y-.495 (Coordinate System);
G43 H4 M3 S400 (Tool Length Compensation, Spindle On);
M8 (Collant On); 
G0 Z.1;

G81 X.562 Y-.495 Z-.25 R.1 F2.4;
X1.349;
X2.136;
G80;

G0 Z.1;
M9 (Collant Off);
G91 G28 Z0. M5 (Z-Home, Spindle Off); 
G91 G28 X0. Y0. (XY-Home); 
M1 (Spindle Stop);

(----------Jobber Drill Operation----------);
N40 M6 T5 (Jobber Drill);
G90 (Absolute Position);
G54 G0 X.562 Y-.495 (Coordinate System);
G43 H5 M3 S400 (Tool Length Compensation, Spindle On);
M8 (Collant On); 
G0 Z.1;

G83 X.562 Y-.495 Z-2. R.1 Q.075 F2.4;
X1.349;
X2.136;
G80;

G0 Z.1;
M9 (Collant Off);
G91 G28 Z0. M5 (Z-Home, Spindle Off); 
G91 G28 X0. Y0. (XY-Home); 
M1 (Spindle Stop);

(----------Reaming Operation----------);
N50 M6 T6 (5/8" Endmill);
G90 (Absolute Position);
G54 G0 X.562 Y-.495 (Coordinate System);
G43 H6 M3 S4000 (Tool Length Compensation, Spindle On);
M8 (Collant On); 
G0 Z.1;

G73 X.562 Y-.495 Z-1.25 R.1 P1. F12.;
X1.349;
X2.136;
G80;

G0 Z.1;
M9 (Collant Off);
G91 G28 Z0. M5 (Z-Home, Spindle Off); 
G91 G28 X0. Y0. (XY-Home); 
M1 (Force Spindle Stop);

(----------Flip Part----------);

(----------Shutdown Operation----------);
N200 M9; (Collant Off);
G53 G49 M5; (Spindle Off);
M30;
%








