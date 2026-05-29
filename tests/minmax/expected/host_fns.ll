define double @min(double %a, double %b) {
entry:
  %cmp0 = fcmp oge double %a, %b
  br i1 %cmp0, label %L1, label %fallthrough0

fallthrough0:
  ret double %a

L1:
  ret double %b
}

define double @max(double %a, double %b) {
entry:
  %cmp0 = fcmp ole double %a, %b
  br i1 %cmp0, label %L2, label %fallthrough0

fallthrough0:
  ret double %a

L2:
  ret double %b
}
