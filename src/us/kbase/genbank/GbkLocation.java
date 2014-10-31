package us.kbase.genbank;

public class GbkLocation extends GbkElement {
    public int strand = 0;
	public int start = 0;
	public int stop = 0;

	public GbkLocation(int lineNum, String type, String value) {
		super(lineNum, type, value);
	}
	
	@Override
	public String toString() {
		return (strand > 0 ? "+" : "-") + "(" + start + ".." + stop + ")";
	}
}
