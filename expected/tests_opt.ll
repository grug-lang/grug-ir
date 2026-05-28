; ModuleID = '.output/tests_unopt.ll'
source_filename = "llvm-link"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-linux-gnu"

@str = private unnamed_addr constant [50 x i8] c"All host function assertions passed successfully!\00", align 1

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define double @min(double %a, double %b) local_unnamed_addr #0 {
entry:
  %cmp0 = fcmp oge double %a, %b
  %b.a = select i1 %cmp0, double %b, double %a
  ret double %b.a
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define double @max(double %a, double %b) local_unnamed_addr #0 {
entry:
  %cmp0 = fcmp ole double %a, %b
  %b.a = select i1 %cmp0, double %b, double %a
  ret double %b.a
}

; Function Attrs: nofree nounwind sspstrong uwtable
define dso_local noundef i32 @main() local_unnamed_addr #1 {
  %1 = tail call i32 @puts(ptr nonnull dereferenceable(1) @str)
  ret i32 0
}

; Function Attrs: nofree nounwind
declare noundef i32 @puts(ptr noundef readonly captures(none)) local_unnamed_addr #2

attributes #0 = { mustprogress nofree norecurse nosync nounwind willreturn memory(none) }
attributes #1 = { nofree nounwind sspstrong uwtable "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #2 = { nofree nounwind }

!llvm.ident = !{!0}
!llvm.errno.tbaa = !{!1}
!llvm.module.flags = !{!5, !6, !7, !8}

!0 = !{!"clang version 22.1.5"}
!1 = !{!2, !2, i64 0}
!2 = !{!"int", !3, i64 0}
!3 = !{!"omnipotent char", !4, i64 0}
!4 = !{!"Simple C/C++ TBAA"}
!5 = !{i32 1, !"wchar_size", i32 4}
!6 = !{i32 8, !"PIC Level", i32 2}
!7 = !{i32 7, !"PIE Level", i32 2}
!8 = !{i32 7, !"uwtable", i32 2}
