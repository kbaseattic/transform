package us.kbase.genbank;

import java.util.*;

/**
 * Parsing of header of contig object (GbkParser). 
 * It could be more than one in typical contig. 
 * @author rsutormin
 */
public class GbkHeader extends GbkElement {
	public List<GbkSubheader> subheaders;

	public GbkHeader(int line_num,String type,String value) {
		super(line_num,type,value);
		this.subheaders = new ArrayList<GbkSubheader>();
	}
	public void save(GbkLocus l, GbkCallback ret, String filename) throws Exception {
		ret.addHeaderTrackFile(l.name, type, getValue(), subheaders, filename);
	}
}
