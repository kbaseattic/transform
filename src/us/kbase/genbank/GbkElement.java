package us.kbase.genbank;

/**
 * Ancestor class for all gbk-parsing classes.
 * @author rsutormin
 */
public class GbkElement {
	public int line_num;
	public String type;
	public StringBuffer value = null;
	public GbkElement(int line_num,String type,String value) {
		super();
		this.line_num = line_num;
		this.type = type;
		if (value != null)
			this.value = new StringBuffer(value);
	}
	public void appendValue(String v) {
		value.append(" ").append(v);
	}	
	public void appendValueWithoutSpace(String v) {
		value.append(v);
	}

    public String getValue() {
        return value.toString();
    }
}
