; ModuleID = 'tests.c'
source_filename = "tests.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-linux-gnu"

@.str = private unnamed_addr constant [22 x i8] c"min(5.0, 10.0) == 5.0\00", align 1
@.str.1 = private unnamed_addr constant [8 x i8] c"tests.c\00", align 1
@__PRETTY_FUNCTION__.main = private unnamed_addr constant [11 x i8] c"int main()\00", align 1
@.str.2 = private unnamed_addr constant [22 x i8] c"min(10.0, 5.0) == 5.0\00", align 1
@.str.3 = private unnamed_addr constant [24 x i8] c"min(3.14, 3.14) == 3.14\00", align 1
@.str.4 = private unnamed_addr constant [23 x i8] c"max(5.0, 10.0) == 10.0\00", align 1
@.str.5 = private unnamed_addr constant [23 x i8] c"max(10.0, 5.0) == 10.0\00", align 1
@.str.6 = private unnamed_addr constant [24 x i8] c"max(3.14, 3.14) == 3.14\00", align 1
@str = private unnamed_addr constant [50 x i8] c"All host function assertions passed successfully!\00", align 1

; Function Attrs: nounwind sspstrong uwtable
define dso_local noundef i32 @main() local_unnamed_addr #0 {
  %1 = tail call double @min(double noundef 5.000000e+00, double noundef 1.000000e+01) #4
  %2 = fcmp oeq double %1, 5.000000e+00
  br i1 %2, label %4, label %3

3:                                                ; preds = %0
  tail call void @__assert_fail(ptr noundef nonnull @.str, ptr noundef nonnull @.str.1, i32 noundef 10, ptr noundef nonnull @__PRETTY_FUNCTION__.main) #5
  unreachable

4:                                                ; preds = %0
  %5 = tail call double @min(double noundef 1.000000e+01, double noundef 5.000000e+00) #4
  %6 = fcmp oeq double %5, 5.000000e+00
  br i1 %6, label %8, label %7

7:                                                ; preds = %4
  tail call void @__assert_fail(ptr noundef nonnull @.str.2, ptr noundef nonnull @.str.1, i32 noundef 11, ptr noundef nonnull @__PRETTY_FUNCTION__.main) #5
  unreachable

8:                                                ; preds = %4
  %9 = tail call double @min(double noundef 3.140000e+00, double noundef 3.140000e+00) #4
  %10 = fcmp oeq double %9, 3.140000e+00
  br i1 %10, label %12, label %11

11:                                               ; preds = %8
  tail call void @__assert_fail(ptr noundef nonnull @.str.3, ptr noundef nonnull @.str.1, i32 noundef 12, ptr noundef nonnull @__PRETTY_FUNCTION__.main) #5
  unreachable

12:                                               ; preds = %8
  %13 = tail call double @max(double noundef 5.000000e+00, double noundef 1.000000e+01) #4
  %14 = fcmp oeq double %13, 1.000000e+01
  br i1 %14, label %16, label %15

15:                                               ; preds = %12
  tail call void @__assert_fail(ptr noundef nonnull @.str.4, ptr noundef nonnull @.str.1, i32 noundef 15, ptr noundef nonnull @__PRETTY_FUNCTION__.main) #5
  unreachable

16:                                               ; preds = %12
  %17 = tail call double @max(double noundef 1.000000e+01, double noundef 5.000000e+00) #4
  %18 = fcmp oeq double %17, 1.000000e+01
  br i1 %18, label %20, label %19

19:                                               ; preds = %16
  tail call void @__assert_fail(ptr noundef nonnull @.str.5, ptr noundef nonnull @.str.1, i32 noundef 16, ptr noundef nonnull @__PRETTY_FUNCTION__.main) #5
  unreachable

20:                                               ; preds = %16
  %21 = tail call double @max(double noundef 3.140000e+00, double noundef 3.140000e+00) #4
  %22 = fcmp oeq double %21, 3.140000e+00
  br i1 %22, label %24, label %23

23:                                               ; preds = %20
  tail call void @__assert_fail(ptr noundef nonnull @.str.6, ptr noundef nonnull @.str.1, i32 noundef 17, ptr noundef nonnull @__PRETTY_FUNCTION__.main) #5
  unreachable

24:                                               ; preds = %20
  %25 = tail call i32 @puts(ptr nonnull dereferenceable(1) @str)
  ret i32 0
}

declare double @min(double noundef, double noundef) local_unnamed_addr #1

; Function Attrs: cold noreturn nounwind
declare void @__assert_fail(ptr noundef, ptr noundef, i32 noundef, ptr noundef) local_unnamed_addr #2

declare double @max(double noundef, double noundef) local_unnamed_addr #1

; Function Attrs: nofree nounwind
declare noundef i32 @puts(ptr noundef readonly captures(none)) local_unnamed_addr #3

attributes #0 = { nounwind sspstrong uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #2 = { cold noreturn nounwind "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #3 = { nofree nounwind }
attributes #4 = { nounwind }
attributes #5 = { cold noreturn nounwind }

!llvm.module.flags = !{!0, !1, !2, !3}
!llvm.ident = !{!4}
!llvm.errno.tbaa = !{!5}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{!"clang version 22.1.5"}
!5 = !{!6, !6, i64 0}
!6 = !{!"int", !7, i64 0}
!7 = !{!"omnipotent char", !8, i64 0}
!8 = !{!"Simple C/C++ TBAA"}
