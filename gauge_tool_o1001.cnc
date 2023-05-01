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
M06 T03 (1/4" Carbide Endmill, 3 Flute, 3/8" LOC);
M01 (Optional Program Stop);
G54 G00 X-.5 Y.125 (Coordinate System);
G43 H03 Z1.0 (Tool Length Compensation);
M03 S4000 (Spindle Forward Command);
M08 (Collant On);
G01 Z0.0 F18.;
;
M98 P1002 L4 (Run subroutine 4 times);
;
G00 Z.1 M09 (Rapid Retract, Collant Off);
G53 G49 Z0.0 M05 (Z Home, Spindle Off);
G53 Y0.0 (Y Home);
M30 (End Program);
%
