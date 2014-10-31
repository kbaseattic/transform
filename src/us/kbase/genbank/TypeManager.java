package us.kbase.genbank;

import java.io.*;
import java.util.*;

public class TypeManager {
	private Set<String> typeHash = new HashSet<String>();
	//
	public TypeManager(String resource) throws Exception {
		this(new BufferedReader(new InputStreamReader(TypeManager.class.getResourceAsStream(resource))));
	}
	public TypeManager(BufferedReader br) throws Exception {
		this(loadLines(br));
	}
	public TypeManager(String[] types) throws Exception {
        for (String type : types) {
            typeHash.add(type.toUpperCase());
        }
	}
	public boolean isType(String type) {
		return typeHash.contains(type.toUpperCase());
	}
	
	private static String[] loadLines(BufferedReader br) throws Exception {
		Vector<String> ret = new Vector<String>();
		for(;;) {
			String line = br.readLine();
			if(line==null) break;
			line = line.trim();
			if(line.length()==0) continue;
			ret.add(line);
		}
		br.close();
		return ret.toArray(new String[ret.size()]);
	}
}
