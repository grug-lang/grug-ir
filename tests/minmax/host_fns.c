#include <stdbool.h>

// Forward declaration of the runtime failure handler implemented in main.c
void assert_failed(void);

double min(double a, double b) {
    return a < b ? a : b;
}

double max(double a, double b) {
    return a > b ? a : b;
}

void assert(bool condition) {
    if (!condition) {
        assert_failed();
    }
}
