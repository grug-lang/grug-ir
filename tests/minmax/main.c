#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <llvm-c/Core.h>
#include <llvm-c/IRReader.h>
#include <llvm-c/Linker.h>
#include <llvm-c/ExecutionEngine.h>
#include <llvm-c/Target.h>
#include <llvm-c/Transforms/PassBuilder.h>

void assert_failed(void) {
    fprintf(stderr, "Runtime Error: Assertion failed!\n");
    exit(1);
}

int main(void) {
    LLVMInitializeNativeTarget();
    LLVMInitializeNativeAsmPrinter();
    LLVMInitializeNativeAsmParser();
    LLVMLinkInMCJIT();

    LLVMContextRef context = LLVMContextCreate();
    char *error_msg = NULL;

    LLVMMemoryBufferRef mod_buf = NULL;
    if (LLVMCreateMemoryBufferWithContentsOfFile("tests/minmax/.output/creeper-Entity.ll", &mod_buf, &error_msg)) {
        fprintf(stderr, "Failed to read creeper-Entity.ll: %s\n", error_msg);
        LLVMDisposeMessage(error_msg);
        return 1;
    }

    LLVMModuleRef mod_module = NULL;
    if (LLVMParseIRInContext(context, mod_buf, &mod_module, &error_msg)) {
        fprintf(stderr, "Failed to parse creeper-Entity.ll: %s\n", error_msg);
        LLVMDisposeMessage(error_msg);
        return 1;
    }

    LLVMMemoryBufferRef host_buf = NULL;
    if (LLVMCreateMemoryBufferWithContentsOfFile("tests/minmax/.output/host_fns.ll", &host_buf, &error_msg)) {
        fprintf(stderr, "Failed to read host_fns.ll: %s\n", error_msg);
        LLVMDisposeMessage(error_msg);
        return 1;
    }

    LLVMModuleRef host_module = NULL;
    if (LLVMParseIRInContext(context, host_buf, &host_module, &error_msg)) {
        fprintf(stderr, "Failed to parse host_fns.ll: %s\n", error_msg);
        LLVMDisposeMessage(error_msg);
        return 1;
    }

    if (LLVMLinkModules2(mod_module, host_module)) {
        fprintf(stderr, "Failed to link modules\n");
        return 1;
    }

    LLVMPassBuilderOptionsRef pb_opts = LLVMCreatePassBuilderOptions();
    LLVMErrorRef pass_err = LLVMRunPasses(mod_module, "default<O3>", NULL, pb_opts);
    LLVMDisposePassBuilderOptions(pb_opts);
    
    if (pass_err) {
        char *pass_err_msg = LLVMGetErrorMessage(pass_err);
        fprintf(stderr, "Failed to run inlining pass: %s\n", pass_err_msg);
        LLVMDisposeErrorMessage(pass_err_msg);
        return 1;
    }

    if (LLVMPrintModuleToFile(mod_module, "tests/minmax/.output/mods.ll", &error_msg)) {
        fprintf(stderr, "Failed to print optimized module: %s\n", error_msg);
        LLVMDisposeMessage(error_msg);
        return 1;
    }

    LLVMExecutionEngineRef engine = NULL;
    if (LLVMCreateExecutionEngineForModule(&engine, mod_module, &error_msg)) {
        fprintf(stderr, "Failed to create execution engine: %s\n", error_msg);
        LLVMDisposeMessage(error_msg);
        return 1;
    }

    LLVMValueRef assert_failed_fn = LLVMGetNamedFunction(mod_module, "assert_failed");
    if (assert_failed_fn) {
        LLVMAddGlobalMapping(engine, assert_failed_fn, (void *)&assert_failed);
    }

    typedef void (*tick_fn_t)(void);
    uint64_t tick_addr = LLVMGetFunctionAddress(engine, "tick");
    
    if (!tick_addr) {
        fprintf(stderr, "Failed to find function 'tick' in module\n");
        return 1;
    }
    
    tick_fn_t tick = (tick_fn_t)tick_addr;
    tick();

    printf("All assertions passed successfully!\n");
    LLVMDisposeExecutionEngine(engine);
    LLVMContextDispose(context);
}
