declare void @assert_failed()
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

define void @assert(i1 %condition) {
entry:
  %cmp0 = icmp ne i1 %condition, 0
  br i1 %cmp0, label %L3, label %fallthrough0

fallthrough0:
  call void @assert_failed()
  br label %L3

L3:
  ret void
}
