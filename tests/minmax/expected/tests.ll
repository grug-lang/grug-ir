; CHECK-LABEL: define dso_local noundef i32 @main
; CHECK-NEXT:  {{%[0-9]+}} = tail call i32 @puts(ptr nonnull dereferenceable(1) @str)
; CHECK-NEXT:  ret i32 0
; CHECK-NEXT: }
