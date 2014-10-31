package us.kbase.genbank;

/**
 * Parsing of sub-headers in contig (GbkParser). 
 * @author rsutormin
 */
public class GbkSubheader extends GbkElement {
	
	public GbkSubheader(int line_num,String type,String value) {
		super(line_num,type,value);
	}
	
	@Override
	public String toString() {
		return "GbkSubheader(" + type + "=>" + value + ")";
	}
}
