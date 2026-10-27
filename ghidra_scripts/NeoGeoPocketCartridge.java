// Sets up a Neo Geo Pocket (Color) cartridge image imported as a raw binary at 0x200000 with the TLCS900H language:
// makes the cartridge block read-only (so that jump tables in it are trusted), labels the 64-byte header and starts
// disassembly at the start address given in the header (offset 1CH).
//@category TLCS900H
//@menupath Analysis.TLCS900H.Neo Geo Pocket cartridge setup

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.data.ByteDataType;
import ghidra.program.model.data.DWordDataType;
import ghidra.program.model.data.WordDataType;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.SourceType;

public class NeoGeoPocketCartridge extends GhidraScript {

	@Override
	protected void run() throws Exception {
		MemoryBlock rom = currentProgram.getMemory().getBlock(toAddr(0x200000));
		if (rom == null) {
			printerr("no memory block at 0x200000: import the cartridge image as a raw binary with base address 0x200000");
			return;
		}
		rom.setWrite(false);
		Address h = rom.getStart();
		String copyright = new String(getBytes(h, 28), "US-ASCII");
		if (!copyright.contains("SNK")) {
			printerr("no SNK license string at 0x200000: not a Neo Geo Pocket cartridge header");
			return;
		}
		createAsciiString(h, 28);
		createLabel(h, "cart_license", true, SourceType.IMPORTED);
		createData(h.add(0x1c), new DWordDataType());
		createLabel(h.add(0x1c), "cart_start_address", true, SourceType.IMPORTED);
		createData(h.add(0x20), new WordDataType());
		createLabel(h.add(0x20), "cart_id", true, SourceType.IMPORTED);
		createData(h.add(0x22), new ByteDataType());
		createLabel(h.add(0x22), "cart_version", true, SourceType.IMPORTED);
		createData(h.add(0x23), new ByteDataType());
		createLabel(h.add(0x23), "cart_system", true, SourceType.IMPORTED);
		createAsciiString(h.add(0x24), 12);
		createLabel(h.add(0x24), "cart_title", true, SourceType.IMPORTED);
		Address entry = toAddr(Integer.toUnsignedLong(getInt(h.add(0x1c))));
		addEntryPoint(entry);
		createLabel(entry, "start", true, SourceType.IMPORTED);
		disassemble(entry);
		createFunction(entry, "start");
		println("cartridge start address " + entry);
	}
}
