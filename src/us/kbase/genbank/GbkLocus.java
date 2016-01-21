package us.kbase.genbank;

/**
 * Pasing of the whole contig object (GbkParser). Every 
 * GBK-file can contain more than one contig object. 
 * @author rsutormin
 */
public class GbkLocus {
	public int line_num;
	public String name;
	private GbkHeader curHeader;
	private GbkFeature curFeature;
	private GbkCallback ret;
	private boolean isClosed = false;
	//
	public GbkLocus(int line_num, String name, GbkCallback ret) throws Exception {
		super();
		this.line_num = line_num;
		this.name = name;
		this.ret = ret;
	}
	public void close(String filename) throws Exception {
		if (isClosed)
            return;
        isClosed = true;
        if (curHeader != null) {
        	curHeader.save(this, ret, filename);
        	curHeader = null;
        }
		if(curFeature!=null) {
			curFeature.save(this, ret, filename);
			curFeature = null;
		}
	}

	public void addHeader(GbkHeader h,String filename) throws Exception {
		if (curHeader != null) {
			curHeader.save(this, ret, filename);
		}
		curHeader = h;
	}

    public void closeHeaders(String filename) throws Exception {
		if (curHeader != null) {
			curHeader.save(this, ret, filename);
			curHeader = null;
		}
    }

	public void addFeature(GbkFeature ft, String filename) throws Exception {
		if (curHeader != null) {
			curHeader.save(this, ret, filename);
			curHeader = null;
		}
		if(curFeature!=null) {
			curFeature.save(this, ret, filename);
		}
		curFeature = ft;
	}

	public boolean isClosed() {
		return isClosed;
	}
}
