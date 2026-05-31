declare void @assert_failed()
define void @assert(i1 %condition) {
entry:
  %cmp0 = icmp ne i1 %condition, 0
  br i1 %cmp0, label %L1, label %fallthrough0

fallthrough0:
  call void @assert_failed()
  br label %L1

L1:
  ret void
}
