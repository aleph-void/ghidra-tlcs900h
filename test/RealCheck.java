// Real-code check for a Neo Geo Pocket (Color) cartridge image imported raw at 0x200000 (no analysis): run the
// module's NeoGeoPocketCartridge.java (header, read-only ROM, entry point), analyse, then report counts and write
// the listing ("<address> <bytes> <text>") for the comparison with unidasm.
// Script args: <listing-out> <report-out>
//@category Testing

import java.io.PrintStream;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Bookmark;
import ghidra.program.model.listing.BookmarkType;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;

public class RealCheck extends GhidraScript {

	@Override
	protected void run() throws Exception {
		String[] args = getScriptArgs();
		// the module's cartridge script: read-only ROM, header labels, entry from the header
		runScript("NeoGeoPocketCartridge.java");
		Address entry = toAddr(Integer.toUnsignedLong(getInt(toAddr(0x20001c))));
		analyzeAll(currentProgram);

		PrintStream lst = new PrintStream(args[0]);
		long n = 0;
		InstructionIterator it = currentProgram.getListing().getInstructions(true);
		while (it.hasNext()) {
			Instruction ins = it.next();
			StringBuilder hex = new StringBuilder();
			for (byte b : ins.getBytes()) {
				hex.append(String.format("%02x", b & 0xff));
			}
			lst.printf("%08x %s %s%n", ins.getAddress().getOffset(), hex, ins.toString());
			n++;
		}
		lst.close();

		int bad = 0, err = 0;
		StringBuilder errs = new StringBuilder();
		for (Bookmark bm : iter(currentProgram.getBookmarkManager().getBookmarksIterator(BookmarkType.ERROR))) {
			err++;
			if (bm.getCategory().contains("Bad Instruction")) {
				bad++;
			}
			if (errs.length() < 4000) {
				errs.append("    ").append(bm.getAddress()).append(' ').append(bm.getCategory()).append(": ")
						.append(bm.getComment()).append('\n');
			}
		}
		DecompInterface dec = new DecompInterface();
		dec.openProgram(currentProgram);
		int funcs = 0, fail = 0;
		StringBuilder fails = new StringBuilder();
		for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
			funcs++;
			DecompileResults r = dec.decompileFunction(f, 60, monitor);
			if (r == null || !r.decompileCompleted() || r.getDecompiledFunction() == null) {
				fail++;
				if (fails.length() < 4000) {
					fails.append("    ").append(f.getEntryPoint()).append(' ')
							.append(r == null ? "null" : r.getErrorMessage()).append('\n');
				}
			}
		}
		dec.dispose();
		PrintStream rep = new PrintStream(args[1]);
		rep.printf("entry %s instructions %d functions %d bad-instruction %d error-bookmarks %d decompile-failures %d%n",
			entry, n, funcs, bad, err, fail);
		rep.print(errs);
		rep.print(fails);
		rep.close();
	}

	private static <T> Iterable<T> iter(java.util.Iterator<T> it) {
		return () -> it;
	}
}
