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
	public void close() throws Exception {
		if (isClosed)
            return;
        isClosed = true;
        if (curHeader != null) {
        	curHeader.save(this, ret);
        	curHeader = null;
        }
		if(curFeature!=null) {
			curFeature.save(this, ret);
			curFeature = null;
		}
	}

	public void addHeader(GbkHeader h) throws Exception {
		if (curHeader != null) {
			curHeader.save(this, ret);
		}
		curHeader = h;
	}

    public void closeHeaders() throws Exception {
		if (curHeader != null) {
			curHeader.save(this, ret);
			curHeader = null;
		}
    }

	public void addFeature(GbkFeature ft) throws Exception {
		if (curHeader != null) {
			curHeader.save(this, ret);
			curHeader = null;
		}
		if(curFeature!=null) {
			curFeature.save(this, ret);
		}
		curFeature = ft;
	}

	public boolean isClosed() {
		return isClosed;
	}
}
