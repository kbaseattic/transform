package us.kbase.genbank;

/**
 * Parsing of feature properties (GbkParser). 
 * @author rsutormin
 */
public class GbkQualifier extends GbkElement {
	// is_text and is_closed are currently not used elsewhere in the code:
    boolean is_text = false;
    boolean is_closed = false;
    public GbkQualifier(int line_num,String type,String value) {
		super(line_num,type,value);
    }
    public void close() {
		is_closed = true;
		String val = value.toString();
		if (val.startsWith("\"")) {
			if (val.endsWith("\"")) {
				is_text = true;
				// remove double quotes around text values:
				value.deleteCharAt(0);
				value.deleteCharAt(value.length()-1);
			}
			else {
				throw new RuntimeException("Unbalanced quotes in qualifier: ["+val+"]");
			}
		}
		if ((val.endsWith("\"")) &&
			(!val.startsWith("\""))) {
			throw new RuntimeException("Unbalanced quotes in qualifier: ["+val+"]");
		}
    }
	
    @Override
	public String toString() {
		return "GbkQualifier(" + type + "=>" + value + ")";
    }
}
