#include <stdbool.h>

void assert_failed(void);

void assert(bool condition) {
    if (!condition) {
        assert_failed();
    }
}
