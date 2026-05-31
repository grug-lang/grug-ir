#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

#include <llvm-c/Core.h>
#include <llvm-c/IRReader.h>
#include <llvm-c/Linker.h>
#include <llvm-c/ExecutionEngine.h>
#include <llvm-c/Target.h>
#include <llvm-c/Transforms/PassBuilder.h>

static void fatal(const char *msg) {
    fprintf(stderr, "Error: %s\n", msg);
    exit(EXIT_FAILURE);
}

static void fatal_llvm(const char *context, char *llvm_msg) {
    fprintf(stderr, "Error: %s: %s\n", context, llvm_msg);
    LLVMDisposeMessage(llvm_msg);
    exit(EXIT_FAILURE);
}

static void check_llvm_error(LLVMErrorRef err, const char *context) {
    if (err) {
        char *msg = LLVMGetErrorMessage(err);
        fprintf(stderr, "Error: %s: %s\n", context, msg);
        LLVMDisposeErrorMessage(msg);
        exit(EXIT_FAILURE);
    }
}

static LLVMMemoryBufferRef load_buffer(const char *path) {
    LLVMMemoryBufferRef buffer = NULL;
    char *err = NULL;

    if (LLVMCreateMemoryBufferWithContentsOfFile(path, &buffer, &err)) {
        fatal_llvm(path, err);
    }

    return buffer;
}

static LLVMModuleRef parse_module(LLVMContextRef context, LLVMMemoryBufferRef buffer, const char *name) {
    LLVMModuleRef module = NULL;
    char *err = NULL;

    if (LLVMParseIRInContext(context, buffer, &module, &err)) {
        fatal_llvm(name, err);
    }

    return module;
}

void assert_failed(void) {
    fprintf(stderr, "Runtime Error: Assertion failed!\n");
    exit(EXIT_FAILURE);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <test_name>\n", argv[0]);
        return 1;
    }

    char *test_name = argv[1];
    char creeper_path[256], host_path[256], mods_path[256];

    snprintf(creeper_path, sizeof(creeper_path), "tests/%s/.output/creeper-Entity.ll", test_name);
    snprintf(host_path, sizeof(host_path), "tests/%s/.output/host_fns.ll", test_name);
    snprintf(mods_path, sizeof(mods_path), "tests/%s/.output/mods.ll", test_name);

    LLVMInitializeNativeTarget();
    LLVMInitializeNativeAsmPrinter();
    LLVMInitializeNativeAsmParser();
    LLVMLinkInMCJIT();

    LLVMContextRef context = LLVMContextCreate();
    LLVMModuleRef mod_module = parse_module(context, load_buffer(creeper_path), "creeper-Entity.ll");
    LLVMModuleRef host_module = parse_module(context, load_buffer(host_path), "host_fns.ll");

    if (LLVMLinkModules2(mod_module, host_module)) {
        fatal("Failed to link modules");
    }

    LLVMPassBuilderOptionsRef pb_opts = LLVMCreatePassBuilderOptions();
    LLVMErrorRef pass_err = LLVMRunPasses(mod_module, "default<O3>", NULL, pb_opts);
    LLVMDisposePassBuilderOptions(pb_opts);
    check_llvm_error(pass_err, "Failed to run optimization passes");

    char *err = NULL;
    if (LLVMPrintModuleToFile(mod_module, mods_path, &err)) {
        fatal_llvm("Failed to print optimized module", err);
    }

    LLVMExecutionEngineRef engine = NULL;
    if (LLVMCreateExecutionEngineForModule(&engine, mod_module, &err)) {
        fatal_llvm("Failed to create execution engine", err);
    }

    LLVMValueRef assert_failed_fn = LLVMGetNamedFunction(mod_module, "assert_failed");
    if (assert_failed_fn) {
        LLVMAddGlobalMapping(engine, assert_failed_fn, (void *)&assert_failed);
    }

    uint64_t tick_addr = LLVMGetFunctionAddress(engine, "tick");
    if (!tick_addr) {
        fatal("Failed to find function 'tick'");
    }

    ((void (*)(void))tick_addr)();

    printf("All assertions passed successfully!\n");
    LLVMDisposeExecutionEngine(engine);
    LLVMContextDispose(context);
}
