-f s-parameter file
-vp victim input port comma output port
-ap aggressor input port output port (comma separated and can be multiple)
-pr port reordering of s-parameter file
-se single-ended ports
-vt voltage transfer function
-z0 reference impedances

s-parameter file (-f) is read in.  Then, the port reordering (-pr) is applied.  The new s-parameter file has the number of ports in the port reordering, in that order.
Then, single-ended ports (-se) are applied.  The number of these must match the number of ports surviving the port reordering and are in order p,n,p,n,....  The new ports, after conversion to mixed mode, are all differential followed by all common.  The differential are in order of the first p,n (differential port 1), the second p,n (differential port 2), etc. followed by the common-mode ports.  Then, the reference impedances are applied (-z0).  There must be either one value (applied to all ports), two values (applied to the two ports, or the first value is applied to the differential ports and the second to the common ports) or one value per port surviving the mixed-mode conversion.  Then, if -vt is supplied, all differential and common mode ports are converted to voltage transfer functions.  Finally, the victim input and output (-vip,-vop

