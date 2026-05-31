declare void @assert(i1)
declare double @max(double, double)
declare double @min(double, double)
define void @tick() {
entry:
  %t1 = alloca double
  %call0 = call double @min(double 10.0, double 5.0)
  store double %call0, ptr %t1
  %t2 = alloca i1
  %load0 = load double, ptr %t1
  %op0 = fcmp oeq double %load0, 5.0
  store i1 %op0, ptr %t2
  %load1 = load i1, ptr %t2
  call void @assert(i1 %load1)
  %t3 = alloca double
  %call1 = call double @max(double 10.0, double 5.0)
  store double %call1, ptr %t3
  %t4 = alloca i1
  %load2 = load double, ptr %t3
  %op1 = fcmp oeq double %load2, 10.0
  store i1 %op1, ptr %t4
  %load3 = load i1, ptr %t4
  call void @assert(i1 %load3)
  ret void
}
