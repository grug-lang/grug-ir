; CHECK-LABEL: define void @tick
; CHECK-NEXT: entry:
; CHECK-NEXT: %t1 = alloca double
; CHECK-NEXT: %call0 = call double @min(double 4.0, double 2.0)
; CHECK-NEXT: store double %call0, ptr %t1
; CHECK-NEXT: %load0 = load double, ptr %t1
; CHECK-NEXT: call void @print_number(double %load0)
; CHECK-NEXT: ret void
; CHECK-NEXT: }
