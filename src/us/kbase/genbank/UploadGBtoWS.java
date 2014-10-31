package us.kbase.genbank;

import com.fasterxml.jackson.databind.ObjectMapper;
import us.kbase.kbasegenomes.ContigSet;
import us.kbase.kbasegenomes.Genome;

import java.io.File;
import java.io.IOException;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Created by Marcin Joachimiak
 * User: marcin
 * Date: 10/29/14
 * Time: 3:54 PM
 */
public class UploadGBtoWS {


    /**
     *
     * @param args
     */
    public UploadGBtoWS(String[] args) {

        ContigSet cs = null;
        //load ContigSet object from file
        try {
            ObjectMapper mapper = new ObjectMapper();
            File f1 = new File(args[0]);
            cs = mapper.readValue(f1, ContigSet.class);
        } catch (IOException e) {
            e.printStackTrace();
        }

        Genome gnm = null;
        //load Genome object from file
        try {
            ObjectMapper mapper = new ObjectMapper();
            File f2 = new File(args[1]);
            gnm = mapper.readValue(f2, Genome.class);
        } catch (IOException e) {
            e.printStackTrace();
        }

        Map<String, String> meta = new LinkedHashMap<String, String>();
        meta.put("Scientific name", gnm.getScientificName());

        //GbkUploader.uploadtoWS(wc, ws, gnm.getId(), token, gnm, cs.getId(), cs, meta);
    }

    /**
     * @param args
     */
    public final static void main(String[] args) {
        if (args.length == 2) {
            try {
                UploadGBtoWS u = new UploadGBtoWS(args);
            } catch (Exception e) {
                e.printStackTrace();
            }
        } else {
            System.out.println("usage: java us.kbase.genbank.test.UploadGBtoWS <Genome jsonp> <ContigSet jsonp>");
        }
    }
}
