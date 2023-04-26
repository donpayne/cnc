%
:(Pythagorean Theorem)
:(Example: G65 P9001 A[] C[] V[])
:(A = the length of a known side, local var #1)
:(C = the length of a known hypotenuse, local var #3)
:(V = the var number to store the answer, local var #22)
O9001; 
#[#22] = SQRT[[#3 * #3] - [#1 * #1]];
M99;
%
