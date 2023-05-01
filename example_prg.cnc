#region
$Inches (Alarm if not inches set)
$Mill (Alarm if not a milling machine)
$AddEmbeddedRegPart 11, .787, .787 (Load embedded workpiece)
$ReadTasEmbeddedTool 
#endregion

T55 M6 (Perform tool change) 
G92 X3.543 Y2.756 Z1.181
G0 X-2.953 Y-2.559 M3 S2000 F20
Z-0.197
M98 P1001 L1
Z-0.276
M98 P1001 L1
Z-0.354
M98 P1001 L1

G0 Z.1
T47 M6 (Perform tool change)
G0 Z0.079 X-1.969 Y-1.181 M3 M8 S3000 F22
M98 P1000 L1 (Drill 3 holes)
X1.969 Y-1.181
M98 P1000 L1 (Drill 3 holes)
G90
M1 (Optional stop)

T31 M6 (Perform tool change)
(Milling of contour)
G00 X0 Y-1.599 Z.1
G01 Z-0.5 F50 M08 M3 S3000 
G02 X-1.487 Y-0.588 I0 J1.599 
G03 X-1.603 Y-0.418 I-0.436 J-0.172
G02 X-0.619 Y3.818 I1.71 J1.835
G02 X-0.419 Y3.281 I0.083 J-0.275
G03 X-1.681 Y1.162 I0.864 J-1.95
G03 X-1.246 Y1.003 I0.248 J0.003
G02 X0 Y1.599 I1.246 J-1.003
G02 X1.245 Y1.003 I0 J-1.599
G03 X1.68 Y1.162 I0.187 J0.163
G03 X0.418 Y3.281 I-2.126 J0.169
G02 X0.618 Y3.818 I0.116 J0.263
G02 X1.602 Y-0.418 I-0.725 J-2.401
G03 X1.486 Y-0.588 I0.319 J-0.343
G02 X0 Y-1.599 I-1.487 J0.588
G00 Z0.079 M09
M1 (Optional stop)
T33 M6 (Perform tool change)
(Mill spiral)
G00 X-0.914 Y0 Z.1
G01 Z-0.787 F40 M08 M3 S1875 
G03 I0.913 J0 
G03 X0.597 I0.756 J0
G03 X-0.599 I-0.598 J0
G03 X0.283 I0.441 J0
G03 X-0.284 I-0.283 J0
G03 X-0.032 I0.126 J0
G00 Z0.079 M09
T46 M6 (Perform tool change)
(Circular drilling cycle)
G00 Z0.079 M3 M8 S4000 F22
G12 X0 Y0 Z-.787 R.0787 Q.2 SA0 AS36 RA1.18 H10
G00 Z0.394 M09
M6
($Message "See you at CNCSimulator.com!" 4 0)
M30 (End of program)

(Drilling sub program 1)
O1000
G90 M8 M3
G73 Z-0.8 R0.08 Q0.2 P0 F25
Y3.543
G0 G80 G90 Z0.079
M17

O1001
G1 Y-2.362
G91
Y6.89
X5.906
Y-6.693
X-5.906
Y-0.394
G90
M17


