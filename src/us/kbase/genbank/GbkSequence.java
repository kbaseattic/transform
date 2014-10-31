package us.kbase.genbank;

/**
 * Parsing of dna sequence of contig object (GbkParser). 
 * @author rsutormin
 */
public class GbkSequence {
	private final GbkLocus locus;
    private final GbkCallback ret;
    private StringBuilder seqPart = new StringBuilder();
    private int seqPartNum = 0;
    private int seqCommonLen = 0;

    public static final int MAX_SEQ_PART = 1000000;
	//
	public GbkSequence(GbkLocus l, GbkCallback ret) throws Exception {
		super();
        locus = l;
		this.ret = ret;
	}
	public void append(String seq) throws Exception {
		seqPart.append(seq);
        seqCommonLen += seq.length();
        if (seqPart.length() >= MAX_SEQ_PART) {
            ret.addSeqPart(locus.name, seqPartNum, seqPart.toString(), seqCommonLen);
            seqPartNum++;
            seqPart = new StringBuilder();
        }
	}
	public void close() throws Exception {
		if (seqPart != null && seqPart.length() > 0) {
            ret.addSeqPart(locus.name, seqPartNum, seqPart.toString(), seqCommonLen);
            seqPart = null;
        }
	}
}
