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
	public void append(String seq, String filename) throws Exception {
		seqPart.append(seq);
        seqCommonLen += seq.length();
        if (seqPart.length() >= MAX_SEQ_PART) {
            ret.addSeqPartTrackFile(locus.name, seqPartNum, seqPart.toString(), seqCommonLen, filename);
            seqPartNum++;
            seqPart = new StringBuilder();
        }
	}
	public void close(String filename) throws Exception {
		if (seqPart != null && seqPart.length() > 0) {
            ret.addSeqPartTrackFile(locus.name, seqPartNum, seqPart.toString(), seqCommonLen, filename);
            seqPart = null;
        }
	}
}
