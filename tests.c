#include <assert.h>
#include <stdio.h>

// Declare the host functions generated from output_host_fns.ll
extern double min(double a, double b);
extern double max(double a, double b);

int main() {
    // Test min()
    assert(min(5.0, 10.0) == 5.0);
    assert(min(10.0, 5.0) == 5.0);
    assert(min(3.14, 3.14) == 3.14);

    // Test max()
    assert(max(5.0, 10.0) == 10.0);
    assert(max(10.0, 5.0) == 10.0);
    assert(max(3.14, 3.14) == 3.14);

    printf("All host function assertions passed successfully!\n");
}
