package us.kbase.kbaseenigmametals;

import java.io.File;
import us.kbase.common.service.UObject;
import us.kbase.kbaseenigmametals.WellSampleMatrix;
import us.kbase.kbaseenigmametals.WellSampleMatrixUploader;

public class WellSampleDataImporter {

	private String fileName = null;
	private String token = null;
	private Long workspaceId = null;

	
	public WellSampleDataImporter (String fileName, Long workspaceId, String token) throws Exception{
		if (fileName == null) {
			System.out.println("cMonkey Expression data file name required");
		} else {
			this.fileName = fileName;
		}
		if (token == null) {
			throw new Exception("Token not assigned");
		} else {
			this.token = token;
		}
		
		if (workspaceId == null) {
			throw new Exception("Workspace name not assigned");
		} else {
			this.workspaceId = workspaceId;
		}

	}
	
	public void importMatrix (String matrixName) throws Exception {
		
		WellSampleMatrixUploader uploader = new WellSampleMatrixUploader();
		
		WellSampleMatrix matrix = new WellSampleMatrix();
		matrix.setName(matrixName);
		
		File inputFile = new File(this.fileName);
		
		matrix = uploader.generateWellSampleMatrix(inputFile, matrix);
		//System.out.println(matrix.toString());
		WsDeluxeUtil.saveObjectToWorkspaceRef(UObject.transformObjectToObject(matrix, UObject.class), "KBaseEnigmaMetals.WellSampleMatrix", workspaceId, matrixName, "https://ci.kbase.us/services/ws", token.toString());
	}
	

}
